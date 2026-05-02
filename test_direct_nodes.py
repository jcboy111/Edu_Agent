# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.nodes import heuristic_teaching_node, response_node

state = create_initial_state(topic="奇偶性")
state["apos_level"] = "action"
state["zpd_min"] = 0.3
state["zpd_max"] = 0.6
state["messages"] = [{"role": "user", "content": "什么是奇函数", "timestamp": 0}]

results = []

# Test heuristic_teaching_node
ht_result = heuristic_teaching_node(state)
question = ht_result.get("current_question", "")
bad = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望", "当前话题"]
found_h = [p for p in bad if p in question]

results.append(("heuristic_teaching_node question", question, "PASS" if not found_h else "FAIL " + str(found_h)))

# Test response_node
state["current_question"] = question
resp_result = response_node(state)
messages = resp_result.get("messages", [])
if messages:
    ai_msg = messages[-1].get("content", "")
    found_r = [p for p in bad if p in ai_msg]
    results.append(("response_node message", ai_msg, "PASS" if not found_r else "FAIL " + str(found_r)))

# Write to file
with open('d:/VSwork/Edu_Agent/direct_test_results.txt', 'w', encoding='utf-8') as f:
    f.write("Direct Node Test Results\n")
    f.write("=" * 60 + "\n\n")
    for name, content, status in results:
        f.write(f"=== {name} ===\n")
        f.write(f"Status: {status}\n")
        f.write(f"Content preview:\n{content[:300]}\n")
        f.write("\n" + "-" * 60 + "\n\n")

print("Done. Check direct_test_results.txt")