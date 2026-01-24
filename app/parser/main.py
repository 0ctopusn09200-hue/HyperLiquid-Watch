"""
Parser Service - Hyperliquid WebSocket to Kafka
Subscribes to Hyperliquid trades and publishes parsed messages to Kafka
"""
import asyncio
import os
import signal
import sys
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Dict, Any
from dotenv import load_dotenv

from hl_ws_client import HyperliquidWSClient
from producer import MessageProducer


class ParserService:
    """Main parser service that orchestrates WebSocket client and Kafka producer"""
    
    def __init__(self):
        """Initialize parser service with environment configuration"""
        load_dotenv()
        
        # Configuration from environment
        self.coin = os.getenv("HL_COIN", "BTC")
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "hyperliquid-raw-trades")
        self.dry_run = os.getenv("DRY_RUN", "0") == "1"
        
        # Initialize components
        self.producer = MessageProducer(
            bootstrap_servers=self.kafka_servers,
            topic=self.kafka_topic,
            dry_run=self.dry_run
        )
        
        self.ws_client = HyperliquidWSClient(
            coin=self.coin,
            on_message_callback=self.handle_message
        )
        
        self.running = False
        self.message_count = 0
        
        print("\n" + "="*60)
        print("Hyperliquid Parser Service")
        print("="*60)
        print(f"Coin: {self.coin}")
        print(f"Kafka: {self.kafka_servers}")
        print(f"Topic: {self.kafka_topic}")
        print(f"DRY_RUN: {self.dry_run}")
        print("="*60 + "\n")
    
    async def handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming WebSocket message and convert to Kafka format
        
        Args:
            data: Raw message from Hyperliquid WebSocket
        """
        try:
            # Check if this is a trades message
            channel = data.get("channel")
            if channel != "trades":
                return
            
            # Extract trades data
            trades_data = data.get("data", [])
            if not isinstance(trades_data, list):
                return
            
            # Process each trade
            for trade in trades_data:
                parsed_msg = self.parse_trade(trade, data)
                if parsed_msg:
                    success = self.producer.send_message(parsed_msg)
                    if success:
                        self.message_count += 1
        
        except Exception as e:
            print(f"✗ Error handling message: {e}")
            import traceback
            traceback.print_exc()
    
    def parse_trade(self, trade: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single trade into the required schema format
        
        Schema reference (docs/data_schemas.md):
        - tx_hash: string (unique identifier)
        - block_number: integer
        - block_timestamp: string (ISO 8601)
        - user_address: string
        - coin: string
        - side: string (LONG/SHORT/OPEN/CLOSE)
        - size: string (decimal)
        - price: string (decimal)
        - leverage: string (decimal, optional)
        - margin: string (decimal, optional)
        - fee: string (decimal, optional)
        - tx_type: string (ORDER/LIQUIDATION/etc)
        - raw_data: object (original data)
        
        Args:
            trade: Single trade data from WebSocket
            raw_data: Complete raw message for reference
            
        Returns:
            Parsed message dict matching schema
        """
        try:
            # Generate tx_hash from trade data
            trade_str = json.dumps(trade, sort_keys=True)
            tx_hash = "0x" + hashlib.sha256(trade_str.encode()).hexdigest()
            
            # Extract trade fields with fallbacks
            # Common fields in Hyperliquid trades: px (price), sz (size), side, time
            price_raw = trade.get("px", trade.get("price", "0"))
            size_raw = trade.get("sz", trade.get("size", "0"))
            side_raw = trade.get("side", "").upper()
            timestamp_ms = trade.get("time", None)
            
            # Convert side to schema format
            if side_raw in ["B", "BUY", "LONG"]:
                side = "LONG"
            elif side_raw in ["A", "S", "SELL", "SHORT"]:
                side = "SHORT"
            else:
                side = "OPEN"
            
            # Format timestamp
            if timestamp_ms:
                try:
                    dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc)
                    block_timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                except:
                    block_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            else:
                block_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            
            # Convert numeric values to decimal strings
            def to_decimal_str(value, default="0"):
                try:
                    return str(Decimal(str(value)))
                except:
                    return default
            
            price = to_decimal_str(price_raw, "0")
            size = to_decimal_str(size_raw, "0")
            
            # Calculate fee if available (typically a small percentage)
            fee_raw = trade.get("fee")
            if fee_raw:
                fee = to_decimal_str(fee_raw, "0")
            else:
                # Estimate fee as 0.025% of notional value (typical for spot)
                try:
                    notional = Decimal(price) * Decimal(size)
                    fee = str(notional * Decimal("0.00025"))
                except:
                    fee = "0"
            
            # Build the message according to schema
            message = {
                "tx_hash": tx_hash,
                "block_number": 0,  # Not available in trades data
                "block_timestamp": block_timestamp,
                "user_address": trade.get("user", trade.get("address", "UNKNOWN")),
                "coin": trade.get("coin", self.coin),
                "side": side,
                "size": size,
                "price": price,
                "leverage": to_decimal_str(trade.get("leverage"), None) if "leverage" in trade else None,
                "margin": to_decimal_str(trade.get("margin"), None) if "margin" in trade else None,
                "fee": fee,
                "tx_type": "ORDER",
                "raw_data": trade  # Preserve original trade data
            }
            
            # Remove None values for optional fields
            message = {k: v for k, v in message.items() if v is not None}
            
            return message
        
        except Exception as e:
            print(f"✗ Error parsing trade: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def start(self):
        """Start the parser service"""
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            print("\n⚠ Shutdown signal received, stopping gracefully...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            print("▶ Starting parser service...")
            await self.ws_client.connect()
        except Exception as e:
            print(f"✗ Fatal error: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the parser service gracefully"""
        if not self.running:
            return
        
        print("\n⏹ Stopping parser service...")
        self.running = False
        
        # Close WebSocket
        await self.ws_client.close()
        
        # Flush and close Kafka producer
        self.producer.flush()
        self.producer.close()
        
        print(f"\n✓ Parser service stopped")
        print(f"  Total messages processed: {self.message_count}")
        
        # Exit
        sys.exit(0)


async def main():
    """Main entry point"""
    parser = ParserService()
    await parser.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
