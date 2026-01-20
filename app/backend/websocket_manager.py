"""
WebSocket connection manager and message broadcasting (frontend-compatible)
"""
import json
from typing import Dict, Set, List, Optional
from datetime import datetime
from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections and subscriptions"""
    
    def __init__(self):
        # Store active connections: {websocket: {channels: set, filters: dict}}
        self.active_connections: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = {
            "channels": set(),
            "filters": {}
        }
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
    
    async def subscribe(self, websocket: WebSocket, channels: List[str], filters: Dict = None):
        """Subscribe to channels with filters"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["channels"].update(channels)
            if filters:
                # Merge filters
                current_filters = self.active_connections[websocket]["filters"]
                current_filters.update(filters)
            
            await self.send_personal_message(
                websocket,
                {
                    "type": "subscribed",
                    "payload": {
                        "channels": channels,
                        "message": "Successfully subscribed"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    
    async def unsubscribe(self, websocket: WebSocket, channels: List[str]):
        """Unsubscribe from channels"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["channels"].difference_update(channels)
            
            await self.send_personal_message(
                websocket,
                {
                    "type": "unsubscribed",
                    "payload": {
                        "channels": channels,
                        "message": "Successfully unsubscribed"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    
    def get_subscriptions(self, websocket: WebSocket) -> Dict:
        """Get current subscriptions for a connection"""
        if websocket in self.active_connections:
            return {
                "channels": list(self.active_connections[websocket]["channels"]),
                "filters": self.active_connections[websocket]["filters"]
            }
        return {"channels": [], "filters": {}}
    
    async def send_personal_message(self, websocket: WebSocket, message_type: str, payload: dict):
        """Send message to a specific connection (frontend format)"""
        try:
            message = {
                "type": message_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_channel(self, channel: str, message_type: str, payload: dict):
        """Broadcast message to all connections subscribed to a channel (frontend format)"""
        disconnected = []
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        for websocket, connection_data in self.active_connections.items():
            if channel in connection_data["channels"]:
                # Apply filters if any
                filters = connection_data.get("filters", {})
                
                # Check token filter
                if "token" in filters and payload.get("token"):
                    if payload["token"] != filters["token"]:
                        continue
                
                # Check minValue filter (for whale_activities)
                if "minValue" in filters and payload.get("value"):
                    if payload["value"] < filters["minValue"]:
                        continue
                
                # Check side filter
                if "side" in filters and payload.get("side"):
                    if payload["side"] != filters["side"]:
                        continue
                
                # Check type filter
                if "type" in filters and payload.get("type"):
                    if payload["type"] != filters["type"]:
                        continue
                
                try:
                    message = {
                        "type": message_type,
                        "payload": payload,
                        "timestamp": timestamp
                    }
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to connection: {e}")
                    disconnected.append(websocket)
        
        # Remove disconnected connections
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_whale_activity(self, activity_data: dict):
        """Broadcast whale activity update"""
        await self.broadcast_to_channel("whale_activities", "whale_activity", activity_data)
    
    async def broadcast_price_update(self, price_data: dict):
        """Broadcast price update for liquidation heatmap"""
        await self.broadcast_to_channel("price_updates", "price_update", price_data)
    
    async def broadcast_long_short_ratio(self, ratio_data: dict):
        """Broadcast long/short ratio update"""
        await self.broadcast_to_channel("long_short_ratio", "long_short_ratio", ratio_data)


# Global connection manager instance
manager = ConnectionManager()
