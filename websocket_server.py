"""
WebSocket 服务器 - 流式对话接口
Phase 1: 单实例架构
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import time
import asyncio

from agents.state import StudentState, create_initial_state
from agents.graph import app as langgraph_app

app = FastAPI(title="Math Odyssey AI - WebSocket Server")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 节点处理提示映射 ==========
NODE_HINTS = {
    "supervisor": "正在分析问题...",
    "learning_diagnosis": "正在分析学情...",
    "emotion_detection": "正在感知你的情绪...",
    "heuristic_teaching": "正在思考启发问题...",
    "problem_solving": "正在分析解题思路...",
    "tool_execution": "正在调用工具...",
    "response": "正在组织回复...",
}


# ========== WebSocket 连接管理 ==========
class ConnectionManager:
    """管理 WebSocket 连接"""

    def __init__(self):
        # session_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # session_id -> StudentState
        self.session_states: dict[str, StudentState] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_states[session_id] = create_initial_state("奇偶性")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_states:
            del self.session_states[session_id]

    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)

    def get_state(self, session_id: str) -> Optional[StudentState]:
        return self.session_states.get(session_id)

    def set_state(self, session_id: str, state: StudentState):
        self.session_states[session_id] = state


manager = ConnectionManager()


# ========== 流式事件处理 ==========
async def stream_graph_events(session_id: str, state: StudentState):
    """
    流式执行 LangGraph，每个节点完成时推送事件

    核心逻辑：
    - 首次对话：诊断学情 → 问第一个问题
    - 后续对话：根据学生回答 → 继续追问（苏格拉底式）
    """
    latest_question = None
    final_state = state

    for event in langgraph_app.stream(state):
        if isinstance(event, dict):
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            # 累积状态更新
            final_state.update(node_state)

            # 1. 发送处理中提示
            if node_name in NODE_HINTS:
                await manager.send_json(session_id, {
                    "type": "processing_start",
                    "node": node_name,
                    "hint": NODE_HINTS[node_name]
                })

            # 2. 如果有支架问题产生（来自 heuristic_teaching / problem_solving）
            if node_state.get("current_question") and node_state.get("node_history"):
                last_node = node_state["node_history"][-1] if node_state["node_history"] else node_name
                if last_node in ("heuristic_teaching", "problem_solving"):
                    latest_question = node_state["current_question"]

            # 3. APOS 状态变化检测
            if node_state.get("apos_tracking"):
                for topic, topic_state in node_state["apos_tracking"].items():
                    old_state = manager.get_state(session_id)
                    old_topic_state = old_state.get("apos_tracking", {}).get(topic, {}) if old_state else {}
                    old_level = old_topic_state.get("level")
                    new_level = topic_state.get("level")
                    if old_level and new_level and old_level != new_level:
                        await manager.send_json(session_id, {
                            "type": "apos_changed",
                            "topic": topic,
                            "old_level": old_level,
                            "new_level": new_level,
                            "description": f"你的学情已从 {old_level} 提升到 {new_level}！"
                        })

            # 4. Schema 完成检测
            if node_state.get("schema_completed"):
                current_topic = node_state.get("current_topic", "奇偶性")
                await manager.send_json(session_id, {
                    "type": "schema_completed",
                    "topic": current_topic,
                    "options": [
                        {"id": "next_topic", "label": "继续学习下一个知识点"},
                        {"id": "practice", "label": "综合练习"},
                        {"id": "review", "label": "回顾复习"},
                        {"id": "associate", "label": "跨知识点关联"}
                    ]
                })

        await asyncio.sleep(0.001)

    # 保存最终状态
    manager.set_state(session_id, final_state)

    # 5. 发送问题（每次只发一个问题，等待学生回应）
    if latest_question:
        await manager.send_json(session_id, {
            "type": "ai_content",
            "content": latest_question,
            "is_question": True
        })
    elif final_state.get("messages"):
        # 如果没有新问题但有消息（比如学生首次提问后的响应），发送简短确认
        msgs = final_state.get("messages", [])
        if msgs and msgs[-1].get("role") == "assistant":
            await manager.send_json(session_id, {
                "type": "ai_content",
                "content": msgs[-1].get("content", "收到，继续思考中..."),
                "is_question": True
            })

    # 6. 发送处理完成
    await manager.send_json(session_id, {
        "type": "processing_end"
    })


# ========== WebSocket 端点 ==========
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket 聊天端点

    前端 → 后端:
    - {"type": "user_message", "content": "..."}
    - {"type": "schema_choice", "choice": "next_topic"}

    后端 → 前端:
    - {"type": "processing_start", "node": "...", "hint": "..."}
    - {"type": "ai_content", "content": "...", "is_question": true}
    - {"type": "ai_response", "content": "...", "is_question": false}
    - {"type": "apos_changed", "topic": "...", "old_level": "...", "new_level": "..."}
    - {"type": "schema_completed", "topic": "...", "options": [...]}
    - {"type": "processing_end"}
    """
    await manager.connect(session_id, websocket)

    try:
        # 初始化状态
        state = manager.get_state(session_id)

        # 监听前端消息
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "user_message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                # 添加用户消息
                state["messages"] = state.get("messages", []) + [
                    {"role": "user", "content": content, "timestamp": time.time()}
                ]
                state["next_node"] = "supervisor"

                # 流式执行图
                await stream_graph_events(session_id, state)

                # 更新状态
                manager.set_state(session_id, state)

            elif data.get("type") == "schema_choice":
                choice = data.get("choice")
                topic = data.get("topic", "奇偶性")

                # 处理 Schema 分流
                if choice == "next_topic":
                    # 切换到下一个知识点，重置状态
                    state = create_initial_state("单调性")  # TODO: 获取下一个推荐知识点
                    manager.set_state(session_id, state)
                    await manager.send_json(session_id, {
                        "type": "topic_changed",
                        "topic": state["current_topic"]
                    })
                elif choice == "practice":
                    await manager.send_json(session_id, {
                        "type": "practice_mode",
                        "topic": topic
                    })
                elif choice == "review":
                    await manager.send_json(session_id, {
                        "type": "review_mode",
                        "topic": topic
                    })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_json(session_id, {
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(session_id)


# ========== HTTP 端点（健康检查）==========
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Math Odyssey AI WebSocket Server"}


@app.get("/")
async def root():
    return {
        "service": "Math Odyssey AI",
        "websocket": "/ws/chat/{session_id}",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
