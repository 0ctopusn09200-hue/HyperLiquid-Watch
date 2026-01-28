"""
Hyperliquid WebSocket Client for subscribing to trades
"""
import asyncio
import json
import websockets
from typing import Callable, Optional, List, Dict, Any


class HyperliquidWSClient:
    """WebSocket client for Hyperliquid exchange"""
    
    # Hyperliquid WebSocket endpoint
    WS_URL = "wss://api.hyperliquid.xyz/ws"
    
    def __init__(self, coin: str, on_message_callback: Callable, subscriptions: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize WebSocket client
        
        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH") - used for trades subscription
            on_message_callback: Callback function to handle received messages
            subscriptions: Optional list of subscription configs.
                          If None, defaults to [{"type": "trades", "coin": coin}]
                          
        Example subscriptions:
            [
                {"type": "trades", "coin": "BTC"},
                {"type": "userFills", "user": "0x123..."},
                {"type": "allMids"}
            ]
        """
        self.coin = coin
        self.on_message = on_message_callback
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        
        # Default to trades subscription for backward compatibility
        self.subscriptions = subscriptions if subscriptions is not None else [
            {"type": "trades", "coin": coin}
        ]
    
    async def connect(self):
        """Connect to Hyperliquid WebSocket and subscribe to trades"""
        self.running = True
        reconnect_delay = 1
        max_reconnect_delay = 60
        
        while self.running:
            try:
                print(f"\nConnecting to Hyperliquid WebSocket: {self.WS_URL}")
                
                async with websockets.connect(
                    self.WS_URL,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    self.ws = websocket
                    print(f"✓ Connected to Hyperliquid WebSocket")
                    
                    # Subscribe to all configured channels
                    for sub_config in self.subscriptions:
                        subscribe_msg = {
                            "method": "subscribe",
                            "subscription": sub_config
                        }
                        
                        await websocket.send(json.dumps(subscribe_msg))
                        
                        # Format subscription info for logging
                        sub_type = sub_config.get("type")
                        sub_detail = sub_config.get("coin") or sub_config.get("user") or "global"
                        print(f"✓ Subscribed to {sub_type} ({sub_detail})")
                    
                    # Reset reconnect delay on successful connection
                    reconnect_delay = 1
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.on_message(data)
                        except json.JSONDecodeError as e:
                            print(f"✗ Failed to decode message: {e}")
                        except Exception as e:
                            print(f"✗ Error processing message: {e}")
            
            except websockets.exceptions.ConnectionClosed:
                print(f"✗ WebSocket connection closed")
            except Exception as e:
                print(f"✗ WebSocket error: {e}")
            
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
            await self.ws.close()
            print("✓ WebSocket connection closed")
