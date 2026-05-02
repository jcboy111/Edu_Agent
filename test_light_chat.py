# -*- coding: utf-8 -*-
"""轻量级对话接口 - 模拟自然聊天"""
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import time

# 轻量级对话用的小号 LLM
chat_llm = ChatOpenAI(
    model="MiniMax-M2.7",
    api_key="sk-cp-livIF2YQqaPga9xkSIbaDt5hn6q-v0VHR73g4EYEjuATVdYvxBV_WdxDLRF2zaD-2BGSXQ7BgY1rJ4Jvm1QIUDKNC3pwk8ePpJgAj6xN-PJphGRHB5iFKFI",
    base_url="https://api.minimaxi.com/v1",
    max_tokens=500,
    timeout=30,
)

SYSTEM_PROMPT = """你是一个耐心的数学老师，正在用苏格拉底式提问法教学生理解"奇函数"的概念。

对话规则：
1. 每次只回复一个问题或简短评论（不超过50字）
2. 用对话的方式，像朋友聊天一样
3. 根据学生的回答自然地继续追问
4. 多用"你觉得呢？"、"为什么呢？"、"能举个例子吗？"这样的问句
5. 不要一次说太多，保持对话节奏

当前话题：奇函数
学生当前水平：初学者

开始对话："""

def chat_light(message: str, history: list = None) -> dict:
    """轻量级对话"""
    if history is None:
        history = []

    # 构建消息
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for h in history:
        if h.get("role") == "user":
            messages.append(HumanMessage(content=f"学生：{h['content']}"))
        else:
            messages.append(HumanMessage(content=f"老师：{h['content']}"))
    messages.append(HumanMessage(content=f"学生：{message}"))

    # 调用 LLM
    response = chat_llm.invoke(messages)
    ai_reply = response.content.strip()

    # 更新历史
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": ai_reply}
    ]

    return {
        "reply": ai_reply,
        "history": new_history
    }

# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试轻量级对话")
    print("=" * 60)

    history = []

    # 第一轮
    result = chat_light("什么是奇函数", history)
    print(f"\n学生：什么是奇函数")
    print(f"老师：{result['reply']}")
    history = result['history']

    # 第二轮
    result = chat_light("我理解是对称的", history)
    print(f"\n学生：我理解是对称的")
    print(f"老师：{result['reply']}")
    history = result['history']

    # 第三轮
    result = chat_light("就像照镜子一样", history)
    print(f"\n学生：就像照镜子一样")
    print(f"老师：{result['reply']}")