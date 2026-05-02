# -*- coding: utf-8 -*-
"""
WebSocket 测试客户端
用于测试 websocket_server.py
"""
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://127.0.0.1:8766/ws/test_session_123"

    print("=== WebSocket 测试 ===")
    print(f"连接: {uri}")

    try:
        async with websockets.connect(uri) as ws:
            print("连接成功!")

            # 发送测试消息
            test_message = {
                "type": "user_message",
                "content": "为什么 f(x)=x^2 是偶函数？"
            }
            await ws.send(json.dumps(test_message))
            print(f"已发送: {test_message['content']}")

            # 接收响应
            message_count = 0
            async for message in ws:
                data = json.loads(message)
                message_count += 1
                print(f"\n[收到消息 {message_count}]")
                print(f"类型: {data.get('type')}")

                if data.get('type') == 'processing_start':
                    print(f"节点: {data.get('node')}")
                    print(f"提示: {data.get('hint')}")

                elif data.get('type') == 'ai_content':
                    print(f"AI 内容: {data.get('content', '')[:80]}...")
                    print(f"是否问题: {data.get('is_question')}")

                elif data.get('type') == 'ai_response':
                    print(f"AI 回复: {data.get('content', '')[:100]}...")

                elif data.get('type') == 'apos_changed':
                    print(f"APOS 变化: {data.get('old_level')} → {data.get('new_level')}")
                    print(f"描述: {data.get('description')}")

                elif data.get('type') == 'schema_completed':
                    print(f"Schema 完成!")
                    print(f"选项: {data.get('options')}")

                elif data.get('type') == 'processing_end':
                    print("\n处理完成!")
                    break

                elif data.get('type') == 'error':
                    print(f"错误: {data.get('message')}")
                    break

                if message_count > 20:
                    print("消息过多，停止接收")
                    break

            print(f"\n共接收 {message_count} 条消息")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"连接关闭: {e}")
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
