"""
Hyperliquid WebSocket Client
"""
import asyncio
import json
import traceback
import socket
from typing import Callable, Optional, List, Dict, Any

import websockets


class HyperliquidWSClient:
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

        self.subscriptions = subscriptions if subscriptions is not None else [
            {"type": "trades", "coin": coin}
        ]

    async def connect(self):
        self.running = True
        reconnect_delay = 1
        max_reconnect_delay = 60

        while self.running:
            try:
                print(f"\nConnecting to Hyperliquid WebSocket: {self.WS_URL}")
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

                    for sub_config in self.subscriptions:
                        subscribe_msg = {"method": "subscribe", "subscription": sub_config}
                        await websocket.send(json.dumps(subscribe_msg))
                        sub_type = sub_config.get("type")
                        sub_detail = sub_config.get("coin") or sub_config.get("user") or "global"
                        print(f"✓ Sent subscribe: {sub_type} ({sub_detail})")

                    reconnect_delay = 1

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            print(f"✗ Non-JSON message: {message[:300]}")
                            continue

                        try:
                            await self.on_message(data)
                        except Exception as e:
                            print("✗ Error processing message:", repr(e))
                            traceback.print_exc()

            except Exception as e:
                print("✗ WebSocket error:", repr(e))
                traceback.print_exc()

            if self.running:
                print(f"⟳ Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

    async def close(self):
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
            finally:
                print("✓ WebSocket connection closed")
