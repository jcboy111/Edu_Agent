# -*- coding: utf-8 -*-
"""测试多轮对话状态是否保持"""
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.graph import app

# 模拟第一轮对话
print("=" * 60)
print("第一轮: 学生问 '什么是奇函数'")
print("=" * 60)

state1 = create_initial_state(topic="奇偶性")
state1["messages"] = [{"role": "user", "content": "什么是奇函数", "timestamp": 0}]

result1 = app.invoke(state1)

print(f"消息数: {len(result1.get('messages', []))}")
print(f"APOS: {result1.get('apos_level')}")
print(f"知识掌握度: {result1.get('knowledge_mastery', {}).get('奇偶性')}")

# 模拟第二轮对话（不重新创建状态，直接用第一轮结果）
print("\n" + "=" * 60)
print("第二轮: 学生问 '奇函数有什么性质'（继续上下文）")
print("=" * 60)

# 关键：这里不创建新状态，而是用第一轮的结果
state2 = result1  # 直接使用

# 添加新消息
state2["messages"] = state2["messages"] + [
    {"role": "user", "content": "奇函数有什么性质", "timestamp": 1}
]
state2["next_node"] = "supervisor"

result2 = app.invoke(state2)

print(f"消息数: {len(result2.get('messages', []))}")
print(f"APOS: {result2.get('apos_level')}")
print(f"知识掌握度: {result2.get('knowledge_mastery', {}).get('奇偶性')}")
print(f"节点历史: {' -> '.join(result2.get('node_history', []))}")

# 检查第二轮是否复用了第一轮的状态
print("\n" + "=" * 60)
print("状态保持检查:")
print("=" * 60)
print(f"第二轮使用了第一轮的apos_level: {result2.get('apos_level') == result1.get('apos_level')}")
print(f"第二轮继续使用 '奇偶性' 主题: {result2.get('current_topic') == '奇偶性'}")