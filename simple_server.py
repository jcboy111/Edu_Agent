# -*- coding: utf-8 -*-
"""
简化版对话服务器
直接对话，无复杂 Agent 逻辑
"""
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# LLM
llm = ChatOpenAI(
    model="MiniMax-M2.7",
    api_key="sk-cp-livIF2YQqaPga9xkSIbaDt5hn6q-v0VHR73g4EYEjuATVdYvxBV_WdxDLRF2zaD-2BGSXQ7BgY1rJ4Jvm1QIUDKNC3pwk8ePpJgAj6xN-PJphGRHB5iFKFI",
    base_url="https://api.minimaxi.com/v1",
    max_tokens=500,
    timeout=30,
)

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

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.active_connections[session_id] = ws
        self.histories[session_id] = []

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.histories:
            del self.histories[session_id]

manager = ConnectionManager()

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

                # 发送思考提示
                await websocket.send_json({
                    "type": "processing_start",
                    "node": "thinking",
                    "hint": "思考中..."
                })

                # 获取历史
                history = manager.histories.get(session_id, [])

                # 构建消息
                messages = [SystemMessage(content=SYSTEM_PROMPT)]
                for h in history:
                    if h["role"] == "user":
                        messages.append(HumanMessage(content=f"学生：{h['content']}"))
                    else:
                        messages.append(HumanMessage(content=h['content']))

                # 如果第一条不是学生问的，先加一句引导
                if not history:
                    messages.append(HumanMessage(content=f"学生：{user_msg}"))
                else:
                    messages.append(HumanMessage(content=f"学生：{user_msg}"))

                # 调用 LLM
                response = llm.invoke(messages)
                ai_reply = response.content.strip()

                # 清理回复（移除内部推理）
                if "<think>" in ai_reply:
                    ai_reply = ai_reply.split("</think>")[-1].strip()

                # 更新历史
                if not history:
                    manager.histories[session_id] = [
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": ai_reply}
                    ]
                else:
                    manager.histories[session_id].append({"role": "user", "content": user_msg})
                    manager.histories[session_id].append({"role": "assistant", "content": ai_reply})

                # 发送回复
                await websocket.send_json({
                    "type": "ai_content",
                    "content": ai_reply,
                    "is_question": True
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