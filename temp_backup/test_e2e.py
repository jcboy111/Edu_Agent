# -*- coding: utf-8 -*-
"""端到端测试 - 模拟学生输入问题，系统返回回复"""

import sys
import json
sys.path.insert(0, 'd:/VSwork/Edu_Agent')

from agents.state import create_initial_state
from agents.graph import app

# 测试用例：学生问题
test_questions = [
    "奇函数是什么",
    "奇函数有什么性质",
    "怎么判断函数是奇函数",
]

def run_test(question):
    # 创建初始状态
    state = create_initial_state(topic="奇偶性")
    state["messages"] = [{"role": "user", "content": question, "timestamp": 0}]

    # 运行图
    result = app.invoke(state)

    # 收集输出
    output = {
        "question": question,
        "messages": [],
        "apos_level": result.get("apos_level"),
        "teaching_strategy": result.get("teaching_strategy"),
        "next_node": result.get("next_node"),
        "node_history": result.get("node_history"),
    }

    for msg in result.get("messages", []):
        if msg.get("role") == "assistant":
            output["messages"].append(msg.get("content", ""))

    return output

if __name__ == "__main__":
    results = []
    for q in test_questions:
        try:
            result = run_test(q)
            results.append(result)
        except Exception as e:
            results.append({"question": q, "error": str(e)})

    # 写入文件
    with open('d:/VSwork/Edu_Agent/test_e2e_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Test completed. Results written to test_e2e_results.json")