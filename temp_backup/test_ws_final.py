# -*- coding: utf-8 -*-
import asyncio
import json
import websockets

async def test():
    uri = "ws://127.0.0.1:8766/ws/chat/test_final"
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
    bad = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望", "当前话题", "APOS", "ZPD"]

    with open('d:/VSwork/Edu_Agent/test_ws_final.txt', 'w', encoding='utf-8') as f:
        f.write("AI Content:\n")
        f.write("=" * 60 + "\n")
        for c in results["ai_content"]:
            f.write(c + "\n")
            f.write("-" * 60 + "\n")
            found = [p for p in bad if p in c]
            f.write(f"Check: {'FAIL ' + str(found) if found else 'PASS'}\n\n")

        f.write("\nAI Response:\n")
        f.write("=" * 60 + "\n")
        for c in results["ai_response"]:
            f.write(c + "\n")
            f.write("-" * 60 + "\n")
            found = [p for p in bad if p in c]
            f.write(f"Check: {'FAIL ' + str(found) if found else 'PASS'}\n\n")

asyncio.run(test())
print("Done - check test_ws_final.txt")