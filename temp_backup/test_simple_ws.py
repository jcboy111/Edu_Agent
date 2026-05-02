# -*- coding: utf-8 -*-
import asyncio
import json
import websockets

async def test():
    uri = "ws://127.0.0.1:8766/ws/chat/test123"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "user_message", "content": "什么是奇函数"}))
        async for msg in ws:
            data = json.loads(msg)
            print(f"Type: {data.get('type')}")
            if data.get('type') == 'ai_content':
                print(f"Content: {repr(data.get('content', '')[:100])}")
                print(f"Has <think>: {'<think>' in data.get('content', '')}")
            if data.get('type') == 'processing_end':
                break

asyncio.run(test())