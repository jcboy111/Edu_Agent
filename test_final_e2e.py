# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.graph import app

state = create_initial_state(topic="奇偶性")
state["messages"] = [{"role": "user", "content": "什么是奇函数", "timestamp": 0}]

result = app.invoke(state)

output = []
output.append("=" * 60)
output.append("E2E Test: 什么是奇函数")
output.append("=" * 60)

for msg in result.get("messages", []):
    if msg.get("role") == "assistant":
        content = msg.get("content", "")
        output.append("\n[AI Message]:")
        output.append(content)

        internal_patterns = ["<think>", "让我分析", "用户想让我", "我需要：", "根据当前"]
        found_internal = [p for p in internal_patterns if p in content]
        if found_internal:
            output.append("FAIL - Found: " + str(found_internal))
        else:
            output.append("PASS - No internal reasoning")

output.append("\n[Node History]: " + " -> ".join(result.get("node_history", [])))
output.append("[APOS]: " + str(result.get("apos_level")))

with open('d:/VSwork/Edu_Agent/test_final_e2e_result.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(output))

print("Done. Check test_final_e2e_result.txt")