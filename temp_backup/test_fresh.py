# -*- coding: utf-8 -*-
import asyncio
import json
import websockets
import time

async def test():
    uri = "ws://127.0.0.1:8766/ws/chat/test_fresh_12345"
    results = []

    async with websockets.connect(uri, ping_timeout=120) as ws:
        await ws.send(json.dumps({"type": "user_message", "content": "什么是奇函数"}))

        msg_count = 0
        async for msg in ws:
            msg_count += 1
            data = json.loads(msg)
            t = data.get('type')
            results.append(data)
            print(f"Msg {msg_count}: {t}")  # Simple output

            if t == 'processing_end' or msg_count > 20:
                break

    # Write results
    with open('d:/VSwork/Edu_Agent/test_ws_results.txt', 'w', encoding='utf-8') as f:
        bad = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望", "当前话题"]
        for msg in results:
            t = msg.get('type')
            if t in ['ai_content', 'ai_response']:
                content = msg.get('content', '')
                f.write(f"=== {t} ===\n")
                f.write(content + "\n")
                found = [p for p in bad if p in content]
                f.write(f"Check: {'FAIL ' + str(found) if found else 'PASS'}\n\n")

asyncio.run(test())
print("Done")