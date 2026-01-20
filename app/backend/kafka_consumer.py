"""
Kafka consumer for subscribing to computed data and broadcasting via WebSocket
"""
import json
import asyncio
import threading
from kafka import KafkaConsumer
from typing import Optional
from config import settings
from websocket_manager import manager


class KafkaConsumerService:
    """Service for consuming Kafka messages and broadcasting via WebSocket"""
    
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the main event loop for scheduling async tasks"""
        self.main_loop = loop
    
    def start(self):
        """Start the Kafka consumer in a background thread"""
        if self.running:
            return
        
        try:
            self.consumer = KafkaConsumer(
                settings.kafka_topic_computed_data,
                bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='backend-consumer-group'
            )
            self.running = True
            
            # Start consumer in background thread
            self.thread = threading.Thread(target=self._consume_loop, daemon=True)
            self.thread.start()
            
            print(f"Kafka consumer started, listening to topic: {settings.kafka_topic_computed_data}")
        except Exception as e:
            print(f"Failed to start Kafka consumer: {e}")
            print("Note: Make sure Kafka is running and accessible")
    
    def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        print("Kafka consumer stopped")
    
    def _consume_loop(self):
        """Main consumption loop (runs in background thread)"""
        while self.running:
            try:
                # Poll for messages (synchronous operation)
                message_pack = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        # Schedule async processing in main event loop
                        if self.main_loop and self.main_loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                self._process_message(message.value),
                                self.main_loop
                            )
                        else:
                            # Fallback: create new event loop if main loop not available
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(self._process_message(message.value))
                                loop.close()
                            except Exception as e:
                                print(f"Error processing message: {e}")
            
            except Exception as e:
                print(f"Error in Kafka consumer loop: {e}")
                import time
                time.sleep(1)
    
    async def _process_message(self, message: dict):
        """Process a Kafka message"""
        try:
            data_type = message.get("data_type")
            data = message.get("data", {})
            coin = message.get("coin")
            timestamp = message.get("timestamp")
            
            if data_type == "LONG_SHORT_RATIO":
                # Broadcast long/short ratio update (frontend format)
                total_value = float(data.get("long_position_value", 0)) + float(data.get("short_position_value", 0))
                long_percent = (float(data.get("long_position_value", 0)) / total_value * 100) if total_value > 0 else 50.0
                short_percent = (float(data.get("short_position_value", 0)) / total_value * 100) if total_value > 0 else 50.0
                
                ratio_data = {
                    "longPercent": round(long_percent, 2),
                    "shortPercent": round(short_percent, 2),
                    "longVolume": float(data.get("long_position_value", 0)),
                    "shortVolume": float(data.get("short_position_value", 0)),
                    "longChange24h": 0.0,  # TODO: Calculate from historical data
                    "shortChange24h": 0.0  # TODO: Calculate from historical data
                }
                await manager.broadcast_long_short_ratio(ratio_data)
            
            elif data_type == "LIQUIDATION_MAP":
                # Broadcast price update for liquidation heatmap (frontend format)
                price_levels = data.get("price_levels", [])
                if price_levels:
                    current_price = sum(level.get("price", 0) for level in price_levels) / len(price_levels)
                    points = []
                    for level in price_levels:
                        points.append({
                            "price": float(level.get("price", 0)),
                            "longVol": float(level.get("long_liquidation_value", 0)) / 10000,
                            "shortVol": float(level.get("short_liquidation_value", 0)) / 10000,
                            "current": abs(level.get("price", 0) - current_price) < (current_price * 0.001)
                        })
                    
                    price_data = {
                        "token": coin or "BTC",
                        "currentPrice": current_price,
                        "points": points
                    }
                    await manager.broadcast_price_update(price_data)
            
            elif data_type == "LIQUIDATION":
                # Broadcast whale activity (frontend format)
                from utils.formatters import format_relative_time, truncate_address, format_token_amount
                from datetime import datetime
                from decimal import Decimal
                
                block_timestamp_str = data.get("block_timestamp", "")
                if block_timestamp_str:
                    try:
                        if block_timestamp_str.endswith("Z"):
                            block_timestamp = datetime.fromisoformat(block_timestamp_str.replace("Z", "+00:00"))
                        else:
                            block_timestamp = datetime.fromisoformat(block_timestamp_str)
                    except:
                        block_timestamp = datetime.utcnow()
                else:
                    block_timestamp = datetime.utcnow()
                
                liquidated_size = Decimal(str(data.get("liquidated_size", 0)))
                coin = data.get("coin", "N/A")
                
                activity_data = {
                    "time": format_relative_time(block_timestamp),
                    "address": truncate_address(data.get("user_address", "")),
                    "token": coin,
                    "value": float(data.get("liquidation_value_usd", 0)),
                    "side": "Long" if data.get("side", "").upper() in ["LONG", "L"] else "Short",
                    "type": "Close",  # Liquidations are always closes
                    "amount": format_token_amount(liquidated_size, coin),
                    "timestamp": block_timestamp.isoformat() + "Z",
                    "txHash": data.get("tx_hash")
                }
                await manager.broadcast_whale_activity(activity_data)
        
        except Exception as e:
            print(f"Error processing Kafka message: {e}")


# Global Kafka consumer instance
kafka_consumer = KafkaConsumerService()
