# -*- coding: utf-8 -*-
import asyncio
import json
import websockets
import re

async def test_websocket():
    uri = "ws://127.0.0.1:8766/ws/chat/test_session_debug"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")

            test_message = {
                "type": "user_message",
                "content": "什么是奇函数"
            }
            await ws.send(json.dumps(test_message))
            print(f"Sent")

            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(message)

                    msg_type = data.get('type')
                    if msg_type == 'ai_content':
                        content = data.get('content', '')
                        print(f"Content has <think>: {'<think>' in content}")
                        print(f"Content starts with: {repr(content[:80])}")
                        break
                    elif msg_type == 'processing_end':
                        break
                except asyncio.TimeoutError:
                    print("Timeout")
                    break
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())