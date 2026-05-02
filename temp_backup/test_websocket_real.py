# -*- coding: utf-8 -*-
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://127.0.0.1:8766/ws/chat/test_session_999"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")

            # Send test message
            test_message = {
                "type": "user_message",
                "content": "什么是奇函数"
            }
            await ws.send(json.dumps(test_message))
            print(f"Sent: {test_message['content']}")

            # Receive all messages
            message_count = 0
            all_content = []
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(message)
                    message_count += 1

                    msg_type = data.get('type')
                    if msg_type == 'processing_start':
                        print(f"[{message_count}] Processing: {data.get('node')} - {data.get('hint')}")
                    elif msg_type == 'ai_content':
                        content = data.get('content', '')
                        print(f"[{message_count}] AI Content (is_question={data.get('is_question')}):")
                        print(f"  {content[:200]}..." if len(content) > 200 else f"  {content}")
                        all_content.append(('ai_content', content))
                    elif msg_type == 'ai_response':
                        content = data.get('content', '')
                        print(f"[{message_count}] AI Response:")
                        print(f"  {content[:200]}..." if len(content) > 200 else f"  {content}")
                        all_content.append(('ai_response', content))
                    elif msg_type == 'processing_end':
                        print(f"[{message_count}] Processing END")
                        break
                    elif msg_type == 'error':
                        print(f"[{message_count}] ERROR: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print("Timeout waiting for message")
                    break

            print(f"\nTotal messages: {message_count}")

            # Check for internal reasoning in AI content
            print("\n" + "=" * 60)
            print("Checking for internal reasoning leaks:")
            bad_patterns = ["<think>", "让我分析", "用户是数学老师", "用户想让我", "当前情境", "用户希望", "当前话题", "APOS", "ZPD"]
            found_any = False
            for msg_type, content in all_content:
                found = [p for p in bad_patterns if p in content]
                if found:
                    print(f"FAIL - {msg_type}: Found {found}")
                    found_any = True
            if not found_any:
                print("PASS - No internal reasoning found")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())