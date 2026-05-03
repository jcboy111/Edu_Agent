# -*- coding: utf-8 -*-
"""
简化版对话服务器
直接对话，无复杂 Agent 逻辑
知识图谱集成：追踪学习进度，推荐学习路径
"""
import asyncio
import json
import time
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from knowledge import KnowledgeGraph

# LLM
llm = ChatOpenAI(
    model="MiniMax-M2.7",
    api_key="sk-cp-livIF2YQqaPga9xkSIbaDt5hn6q-v0VHR73g4EYEjuATVdYvxBV_WdxDLRF2zaD-2BGSXQ7BgY1rJ4Jvm1QIUDKNC3pwk8ePpJgAj6xN-PJphGRHB5iFKFI",
    base_url="https://api.minimaxi.com/v1",
    max_tokens=500,
    timeout=30,
)

# 知识图谱
kg = KnowledgeGraph()

# 系统提示
SYSTEM_PROMPT = """你是一个耐心的数学老师，用苏格拉底式提问法教学生理解数学概念。

规则：
1. 每次只说1-2句话
2. 多问问题，少给答案
3. 像朋友聊天一样自然
4. 学生问什么就答什么，不要预设教学流程"""

app = FastAPI()


# 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.histories: dict[str, list] = {}
        self.learned_points: dict[str, list] = {}

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.active_connections[session_id] = ws
        self.histories[session_id] = []
        self.learned_points[session_id] = []

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.histories:
            del self.histories[session_id]
        if session_id in self.learned_points:
            del self.learned_points[session_id]

    def mark_learned(self, session_id: str, point_id: str):
        if point_id not in self.learned_points.get(session_id, []):
            self.learned_points.setdefault(session_id, []).append(point_id)

    def get_learning_progress(self, session_id: str) -> dict:
        learned = self.learned_points.get(session_id, [])
        return {
            "learned_count": len(learned),
            "learned_points": learned,
            "next_recommendation": kg.get_next_learning(learned)
        }


manager = ConnectionManager()


def detect_knowledge_points(text: str, kg: KnowledgeGraph) -> list:
    """根据用户输入检测涉及的知识点"""
    detected = []
    text_lower = text.lower()
    for point in kg.data.get("knowledge_points", []):
        for kw in point.get("keywords", []):
            if kw.lower() in text_lower:
                detected.append(point["id"])
                break
    return detected


def clean_response(text: str) -> str:
    """清理回复中的内部推理内容"""
    text = re.sub(r'<think>.*?', '', text, flags=re.DOTALL)
    skip_patterns = ["用户希望", "当前情境", "用户是", "当前话题", "APOS", "ZPD"]
    for pattern in skip_patterns:
        if pattern in text:
            lines = text.split('\n')
            text = '\n'.join([l for l in lines if pattern not in l])
    return text.strip()


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "user_message":
                user_msg = data.get("content", "").strip()
                if not user_msg:
                    continue

                await websocket.send_json({
                    "type": "processing_start",
                    "node": "thinking",
                    "hint": "思考中..."
                })

                history = manager.histories.get(session_id, [])
                current_points = detect_knowledge_points(user_msg, kg)

                messages = [SystemMessage(content=SYSTEM_PROMPT)]
                for h in history:
                    if h["role"] == "user":
                        messages.append(HumanMessage(content=f"学生：{h['content']}"))
                    else:
                        messages.append(HumanMessage(content=h['content']))

                messages.append(HumanMessage(content=f"学生：{user_msg}"))

                response = llm.invoke(messages)
                ai_reply = response.content.strip()
                ai_reply = clean_response(ai_reply)

                manager.histories[session_id].append({"role": "user", "content": user_msg})
                manager.histories[session_id].append({"role": "assistant", "content": ai_reply})

                for point_id in current_points:
                    manager.mark_learned(session_id, point_id)

                await websocket.send_json({
                    "type": "ai_content",
                    "content": ai_reply,
                    "is_question": True
                })

                progress = manager.get_learning_progress(session_id)
                await websocket.send_json({
                    "type": "learning_progress",
                    "progress": progress
                })

                await websocket.send_json({"type": "processing_end"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(session_id)


@app.get("/")
async def root():
    return {"service": "Simple Chat", "websocket": "/ws/chat/{session_id}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)