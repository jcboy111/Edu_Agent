# -*- coding: utf-8 -*-
import asyncio
import json
import websockets

async def test():
    uri = "ws://127.0.0.1:8766/ws/chat/test_v2"
    results = []

    async with websockets.connect(uri, ping_timeout=60) as ws:
        await ws.send(json.dumps({"type": "user_message", "content": "什么是奇函数"}))

        async for msg in ws:
            data = json.loads(msg)
            t = data.get('type')
            results.append(data)

            if t == 'processing_end':
                break

    # Write raw results to file
    with open('d:/VSwork/Edu_Agent/test_raw_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Analyze
    bad = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望"]

    with open('d:/VSwork/Edu_Agent/test_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("Analysis of WebSocket messages:\n")
        f.write("=" * 60 + "\n\n")

        for msg in results:
            t = msg.get('type')
            if t in ['ai_content', 'ai_response']:
                content = msg.get('content', '')
                f.write(f"Type: {t}\n")
                f.write(f"Content preview: {content[:150]}...\n")
                found = [p for p in bad if p in content]
                f.write(f"Internal reasoning check: {'FAIL ' + str(found) if found else 'PASS'}\n")
                f.write("-" * 60 + "\n\n")

asyncio.run(test())
print("Done. Check test_analysis.txt and test_raw_results.json")