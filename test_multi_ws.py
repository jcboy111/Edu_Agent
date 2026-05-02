# -*- coding: utf-8 -*-
import asyncio
import json
import websockets

async def test_multi_turn():
    uri = "ws://127.0.0.1:8766/ws/chat/test_multi_turn"
    all_messages = []

    async with websockets.connect(uri, ping_timeout=60) as ws:
        # First turn
        print("=== Turn 1: 什么是奇函数 ===")
        await ws.send(json.dumps({"type": "user_message", "content": "什么是奇函数"}))

        async for msg in ws:
            data = json.loads(msg)
            t = data.get('type')
            if t == 'ai_content':
                print(f"Question: {data.get('content', '')[:80]}...")
                all_messages.append(('q', data.get('content', '')))
            elif t == 'ai_response':
                print(f"Response: {data.get('content', '')[:100]}...")
                all_messages.append(('r', data.get('content', '')))
            elif t == 'processing_end':
                break

        # Second turn - with context
        print("\n=== Turn 2: 奇函数有什么性质 (should have context) ===")
        await ws.send(json.dumps({"type": "user_message", "content": "奇函数有什么性质"}))

        async for msg in ws:
            data = json.loads(msg)
            t = data.get('type')
            if t == 'ai_content':
                print(f"Question: {data.get('content', '')[:80]}...")
                all_messages.append(('q', data.get('content', '')))
            elif t == 'ai_response':
                print(f"Response: {data.get('content', '')[:100]}...")
                all_messages.append(('r', data.get('content', '')))
            elif t == 'processing_end':
                break

    # Analyze
    print("\n" + "=" * 60)
    print("Analysis:")
    print(f"Total messages: {len(all_messages)}")
    print("Questions:", len([m for m in all_messages if m[0] == 'q']))
    print("Responses:", len([m for m in all_messages if m[0] == 'r']))

asyncio.run(test_multi_turn())