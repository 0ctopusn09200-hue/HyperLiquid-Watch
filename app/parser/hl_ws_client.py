"""
Hyperliquid WebSocket Client for subscribing to trades
"""
import asyncio
import json
import traceback
import socket
from typing import Callable, Optional, List, Dict, Any

import websockets


class HyperliquidWSClient:
    """WebSocket client for Hyperliquid exchange"""

    WS_URL = "wss://api.hyperliquid.xyz/ws"

    def __init__(
        self,
        coin: str,
        on_message_callback: Callable,
        subscriptions: Optional[List[Dict[str, Any]]] = None
    ):
        self.coin = coin
        self.on_message = on_message_callback
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False

        # Default subscriptions
        self.subscriptions = subscriptions if subscriptions is not None else [
            {"type": "trades", "coin": coin}
        ]

    async def connect(self):
        """Connect to Hyperliquid WebSocket and subscribe to channels"""
        self.running = True
        reconnect_delay = 1
        max_reconnect_delay = 60

        while self.running:
            try:
                print(f"\nConnecting to Hyperliquid WebSocket: {self.WS_URL}")

                # 连接前做一次 DNS 提示（不影响功能，但能快速定位“解析失败”）
                try:
                    host = self.WS_URL.replace("wss://", "").split("/")[0]
                    ip = socket.gethostbyname(host)
                    print(f"✓ DNS resolved {host} -> {ip}")
                except Exception as e:
                    print(f"✗ DNS resolve failed: {repr(e)}")

                async with websockets.connect(
                    self.WS_URL,
                    ping_interval=20,
                    ping_timeout=10,
                    open_timeout=10,
                    close_timeout=5,
                    max_queue=256,
                ) as websocket:
                    self.ws = websocket
                    print("✓ Connected to Hyperliquid WebSocket")

                    # Subscribe to all configured channels
                    for sub_config in self.subscriptions:
                        subscribe_msg = {
                            "method": "subscribe",
                            "subscription": sub_config
                        }
                        await websocket.send(json.dumps(subscribe_msg))

                        sub_type = sub_config.get("type")
                        sub_detail = sub_config.get("coin") or sub_config.get("user") or "global"
                        print(f"✓ Sent subscribe: {sub_type} ({sub_detail}) -> {subscribe_msg}")

                    # Reset backoff on successful connection
                    reconnect_delay = 1

                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            print(f"✗ Non-JSON message: {message[:300]}")
                            continue

                        # 这里不做任何假设，全部交给上层处理
                        try:
                            await self.on_message(data)
                        except Exception as e:
                            print("✗ Error processing message:", repr(e))
                            traceback.print_exc()

            except websockets.exceptions.InvalidStatusCode as e:
                # 例如 403/404
                print("✗ WebSocket handshake failed (HTTP status):", getattr(e, "status_code", None), repr(e))
                traceback.print_exc()

            except websockets.exceptions.InvalidHandshake as e:
                print("✗ WebSocket invalid handshake:", repr(e))
                traceback.print_exc()

            except websockets.exceptions.ConnectionClosedError as e:
                print(f"✗ WebSocket closed with error: code={e.code} reason={e.reason}")
                traceback.print_exc()

            except websockets.exceptions.ConnectionClosedOK as e:
                print(f"✗ WebSocket closed normally: code={e.code} reason={e.reason}")

            except (asyncio.TimeoutError, TimeoutError) as e:
                print("✗ WebSocket timeout:", repr(e))
                traceback.print_exc()

            except socket.gaierror as e:
                # DNS 解析失败
                print("✗ DNS (gaierror):", repr(e))
                traceback.print_exc()

            except OSError as e:
                # 网络不可达/连接被拒/路由问题/TLS底层错误等经常落到这里
                print("✗ OS/network error:", repr(e))
                traceback.print_exc()

            except Exception as e:
                # 兜底：确保永远能看到异常栈
                print("✗ WebSocket error:", repr(e))
                traceback.print_exc()

            if self.running:
                print(f"⟳ Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            else:
                break

    async def close(self):
        """Close WebSocket connection"""
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
            finally:
                print("✓ WebSocket connection closed")
