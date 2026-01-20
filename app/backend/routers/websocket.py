"""
WebSocket routes for real-time data streaming (frontend-compatible)
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket_manager import manager
from datetime import datetime
from config import settings

# Use prefix to match frontend expectation: /api/v1/ws
router = APIRouter()


@router.websocket(settings.ws_path)
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message (frontend format)
        await manager.send_personal_message(websocket, "connected", {
            "message": "Connected to Hyperliquid data stream"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "subscribe":
                    channels = message.get("channels", [])
                    filters = message.get("filters", {})  # Changed from "params" to "filters"
                    
                    # Validate channels
                    valid_channels = ["whale_activities", "price_updates", "long_short_ratio"]
                    invalid_channels = [ch for ch in channels if ch not in valid_channels]
                    if invalid_channels:
                        await manager.send_personal_message(websocket, "error", {
                            "code": "INVALID_SUBSCRIPTION",
                            "message": f"Invalid channels: {invalid_channels}"
                        })
                    else:
                        await manager.subscribe(websocket, channels, filters)
                
                elif msg_type == "unsubscribe":
                    channels = message.get("channels", [])
                    await manager.unsubscribe(websocket, channels)
                
                elif msg_type == "ping":
                    await manager.send_personal_message(websocket, "pong", {})
                
                elif msg_type == "get_subscriptions":
                    subscriptions = manager.get_subscriptions(websocket)
                    await manager.send_personal_message(websocket, "subscriptions", subscriptions)
                
                else:
                    await manager.send_personal_message(websocket, "error", {
                        "code": "INVALID_MESSAGE",
                        "message": f"Unknown message type: {msg_type}"
                    })
            
            except json.JSONDecodeError:
                await manager.send_personal_message(websocket, "error", {
                    "code": "INVALID_MESSAGE",
                    "message": "Invalid JSON format"
                })
            
            except Exception as e:
                await manager.send_personal_message(websocket, "error", {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
