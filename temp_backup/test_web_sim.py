# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.graph import app

state = create_initial_state(topic="奇偶性")
state["messages"] = [{"role": "user", "content": "什么是奇函数", "timestamp": 0}]
result = app.invoke(state)

ai_messages = [msg.get("content", "") for msg in result.get("messages", []) if msg.get("role") == "assistant"]

with open('d:/VSwork/Edu_Agent/test_result.txt', 'w', encoding='utf-8') as f:
    f.write("Testing: 什么是奇函数\n")
    f.write("=" * 60 + "\n\n")
    all_clean = True
    for i, msg in enumerate(ai_messages):
        f.write(f"[Message {i+1}]:\n")
        f.write(msg + "\n\n")
        bad_patterns = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "设计思路", "需要为他", "用户希望", "当前话题", "APOS", "ZPD"]
        found = [p for p in bad_patterns if p in msg]
        if found:
            f.write(f"FAIL - Found: {found}\n")
            all_clean = False
        else:
            f.write("PASS\n")
        f.write("-" * 60 + "\n")
    f.write("\nOVERALL: " + ("PASS" if all_clean else "FAIL") + "\n")

print("Done. Check test_result.txt")