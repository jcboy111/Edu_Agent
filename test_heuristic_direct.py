# -*- coding: utf-8 -*-
"""直接测试 heuristic_teaching_node 的实际输出"""
import sys
import json
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.nodes import heuristic_teaching_node

# 创建模拟状态
state = create_initial_state(topic="奇偶性")
state["apos_level"] = "action"
state["zpd_min"] = 0.3
state["zpd_max"] = 0.6
state["messages"] = [
    {"role": "user", "content": "什么是奇函数", "timestamp": 0}
]

print("=" * 60)
print("直接测试 heuristic_teaching_node")
print("=" * 60)

result = heuristic_teaching_node(state)

print("\n返回的 current_question:")
print(result.get("current_question", ""))

with open('d:/VSwork/Edu_Agent/test_heuristic_output.txt', 'w', encoding='utf-8') as f:
    f.write("返回的 current_question:\n")
    f.write(result.get("current_question", ""))
    f.write("\n\nnode_history:\n")
    f.write(str(result.get("node_history", [])))
    f.write("\n\npending_tool:\n")
    f.write(str(result.get("pending_tool")))

print("\n已写入 test_heuristic_output.txt")