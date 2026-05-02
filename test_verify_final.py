# -*- coding: utf-8 -*-
import asyncio
import json
import websockets
import sys

async def test():
    uri = "ws://127.0.0.1:8766/ws/chat/test_verify"
    results = {"ai_content": [], "ai_response": []}

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "user_message", "content": "什么是奇函数"}))

        async for msg in ws:
            data = json.loads(msg)
            t = data.get('type')

            if t == 'ai_content':
                results["ai_content"].append(data.get('content', ''))
            elif t == 'ai_response':
                results["ai_response"].append(data.get('content', ''))
            elif t == 'processing_end':
                break

    # Check for internal reasoning
    bad = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望", "当前话题"]

    with open('d:/VSwork/Edu_Agent/test_final_result.txt', 'w', encoding='utf-8') as f:
        f.write("Testing: 什么是奇函数\n")
        f.write("=" * 60 + "\n\n")

        for label, msgs in [("AI Content (问题)", results["ai_content"]), ("AI Response", results["ai_response"])]:
            f.write(f"\n[{label}]:\n")
            f.write("-" * 60 + "\n")
            for msg in msgs:
                f.write(msg + "\n\n")
                found = [p for p in bad if p in msg]
                f.write(f"Internal reasoning check: {'FAIL ' + str(found) if found else 'PASS'}\n")
                f.write("-" * 60 + "\n\n")

asyncio.run(test())