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
        
        # Extended topic configuration (for feature flags)
        # Default to singular form (aligned naming convention)
        self.kafka_topic_liquidations = os.getenv("KAFKA_TOPIC_LIQUIDATIONS", "hyperliquid-raw-liquidation")
        self.kafka_topic_positions = os.getenv("KAFKA_TOPIC_POSITIONS", "hyperliquid-raw-positions")
        self.kafka_topic_prices = os.getenv("KAFKA_TOPIC_PRICES", "hyperliquid-raw-price")
        
        # Feature flags (default: all disabled)
        self.enable_liquidation_feed = os.getenv("ENABLE_LIQUIDATION_FEED", "false").lower() == "true"
        self.enable_position_feed = os.getenv("ENABLE_POSITION_FEED", "false").lower() == "true"
        self.enable_price_feed = os.getenv("ENABLE_PRICE_FEED", "false").lower() == "true"
        
        # Monitored users (required for liquidation/position feeds)
        monitored_users_str = os.getenv("MONITORED_USERS", "")
        self.monitored_users = [u.strip() for u in monitored_users_str.split(",") if u.strip()]
        
        # Initialize components
        self.producer = MessageProducer(
            bootstrap_servers=self.kafka_servers,
            topic=self.kafka_topic,
            dry_run=self.dry_run
        )
        
        # Build subscriptions based on feature flags
        subscriptions = self._build_subscriptions()
        
        self.ws_client = HyperliquidWSClient(
            coin=self.coin,
            on_message_callback=self.handle_message,
            subscriptions=subscriptions
        )
        
        self.running = False
        self.message_count = 0
        
        # Print configuration
        print("\n" + "="*60)
        print("Hyperliquid Parser Service")
        print("="*60)
        print(f"Coin: {self.coin}")
        print(f"Kafka: {self.kafka_servers}")
        print(f"Default Topic: {self.kafka_topic}")
        print(f"DRY_RUN: {self.dry_run}")
        print("─"*60)
        print("Feature Flags:")
        print(f"  Liquidation Feed: {self.enable_liquidation_feed}")
        print(f"  Position Feed: {self.enable_position_feed}")
        print(f"  Price Feed: {self.enable_price_feed}")
        if self.monitored_users:
            print(f"  Monitored Users: {len(self.monitored_users)} address(es)")
        if self.enable_liquidation_feed:
            print(f"  → Liquidations will be sent to: {self.kafka_topic_liquidations}")
        if self.enable_position_feed:
            print(f"  → Positions will be sent to: {self.kafka_topic_positions}")
        if self.enable_price_feed:
            print(f"  → Prices will be sent to: {self.kafka_topic_prices}")
        print("="*60 + "\n")
    
    def _build_subscriptions(self) -> list:
        """
        Build WebSocket subscriptions based on feature flags
        
        Returns:
            List of subscription configs (defaults to trades only)
        """
        subscriptions = [
            {"type": "trades", "coin": self.coin}  # Always subscribe to trades (backward compatible)
        ]
        
        # Add liquidation feed if enabled
        if self.enable_liquidation_feed:
            if not self.monitored_users:
                print("⚠ WARNING: ENABLE_LIQUIDATION_FEED=true but MONITORED_USERS is empty")
                print("  Liquidation feed requires at least one user address. Skipping.")
            else:
                for user_address in self.monitored_users:
                    subscriptions.append({
                        "type": "userFills",
                        "user": user_address
                    })
        
        # Add position feed if enabled
        if self.enable_position_feed:
            if not self.monitored_users:
                print("⚠ WARNING: ENABLE_POSITION_FEED=true but MONITORED_USERS is empty")
                print("  Position feed requires at least one user address. Skipping.")
            else:
                for user_address in self.monitored_users:
                    subscriptions.append({
                        "type": "clearinghouseState",
                        "user": user_address
                    })
        
        # Add price feed if enabled
        if self.enable_price_feed:
            subscriptions.append({
                "type": "allMids"
            })
        
        return subscriptions
    
    async def handle_message(self, data: Dict[str, Any]):
        """
        Handle incoming WebSocket message and convert to Kafka format
        
        Args:
            data: Raw message from Hyperliquid WebSocket
        """
        try:
            channel = data.get("channel")
            
            # Route to appropriate handler based on channel
            if channel == "trades":
                await self._handle_trades(data)
            elif channel == "userFills" and self.enable_liquidation_feed:
                await self._handle_user_fills(data)
            elif channel == "clearinghouseState" and self.enable_position_feed:
                await self._handle_positions(data)
            elif channel == "allMids" and self.enable_price_feed:
                await self._handle_prices(data)
            # Silently ignore other channels (e.g., subscriptionResponse)
        
        except Exception as e:
            print(f"✗ Error handling message: {e}")
            import traceback
            traceback.print_exc()
    
    async def _handle_trades(self, data: Dict[str, Any]):
        """
        Handle trades channel messages (existing logic, unchanged)
        
        Args:
            data: Trades message from WebSocket
        """
        # Extract trades data
        trades_data = data.get("data", [])
        if not isinstance(trades_data, list):
            return
        
        # Process each trade
        for trade in trades_data:
            parsed_msg = self.parse_trade(trade, data)
            if parsed_msg:
                # Send to default topic (backward compatible - no topic override)
                success = self.producer.send_message(parsed_msg)
                if success:
                    self.message_count += 1
    
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
            
            # ========== EXISTING FIELDS (UNCHANGED - DO NOT MODIFY) ==========
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
            
            # ========== NEW FIELDS (OPTIONAL - APPENDED AT END) ==========
            # Extract additional fields for semantic clarity
            # These fields can be safely ignored by old consumers
            
            # Correct order direction semantics (BUY/SELL vs LONG/SHORT)
            if side_raw in ["B", "BUY"]:
                message["order_side"] = "BUY"
            elif side_raw in ["A", "S", "SELL"]:
                message["order_side"] = "SELL"
            else:
                message["order_side"] = "UNKNOWN"
            
            # Extract buyer/seller addresses from users array
            users = trade.get("users", [])
            if len(users) > 0:
                message["buyer_address"] = users[0]
            if len(users) > 1:
                message["seller_address"] = users[1]
            
            # Hyperliquid native identifiers
            if "tid" in trade:
                message["trade_id"] = trade["tid"]
            if "hash" in trade:
                message["trade_hash"] = trade["hash"]
            
            # Remove None values for optional fields
            message = {k: v for k, v in message.items() if v is not None}
            
            return message
        
        except Exception as e:
            print(f"✗ Error parsing trade: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _handle_user_fills(self, data: Dict[str, Any]):
        """
        Handle userFills channel messages (liquidation detection)
        
        Args:
            data: UserFills message from WebSocket
        """
        fills_data = data.get("data", {})
        user = fills_data.get("user")
        fills = fills_data.get("fills", [])
        
        if not isinstance(fills, list):
            return
        
        for fill in fills:
            # Check if this fill is a liquidation
            if "liquidation" in fill and fill["liquidation"]:
                parsed_msg = self.parse_liquidation(fill, user, data)
                if parsed_msg:
                    # Send to liquidation topic
                    success = self.producer.send_message(
                        parsed_msg, 
                        topic=self.kafka_topic_liquidations
                    )
                    if success:
                        self.message_count += 1
    
    async def _handle_positions(self, data: Dict[str, Any]):
        """
        Handle clearinghouseState channel messages (position updates)
        
        Args:
            data: ClearinghouseState message from WebSocket
        """
        state_data = data.get("data", {})
        
        # Extract positions from clearinghouse state
        asset_positions = state_data.get("assetPositions", [])
        margin_summary = state_data.get("marginSummary", {})
        
        if not isinstance(asset_positions, list):
            return
        
        for position in asset_positions:
            parsed_msg = self.parse_position(position, margin_summary, data)
            if parsed_msg:
                # Send to positions topic
                success = self.producer.send_message(
                    parsed_msg,
                    topic=self.kafka_topic_positions
                )
                if success:
                    self.message_count += 1
    
    async def _handle_prices(self, data: Dict[str, Any]):
        """
        Handle allMids channel messages (price updates)
        
        Args:
            data: AllMids message from WebSocket
        """
        mids_data = data.get("data", {})
        mids = mids_data.get("mids", {})
        
        if not isinstance(mids, dict):
            return
        
        # Create a single price update message with all mids
        parsed_msg = self.parse_prices(mids, data)
        if parsed_msg:
            # Send to prices topic
            success = self.producer.send_message(
                parsed_msg,
                topic=self.kafka_topic_prices
            )
            if success:
                self.message_count += 1
    
    def parse_liquidation(self, fill: Dict[str, Any], user: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a liquidation fill into schema format
        
        Args:
            fill: Fill data with liquidation marker
            user: User address from userFills message
            raw_data: Complete raw message for reference
            
        Returns:
            Parsed liquidation message
        """
        try:
            # Generate tx_hash
            fill_str = json.dumps(fill, sort_keys=True)
            tx_hash = "0x" + hashlib.sha256(fill_str.encode()).hexdigest()
            
            # Extract liquidation details
            liquidation_info = fill.get("liquidation", {})
            liquidated_user = liquidation_info.get("liquidatedUser")
            mark_px = liquidation_info.get("markPx", 0)
            method = liquidation_info.get("method", "unknown")  # "market" or "backstop"
            
            # Extract fill details
            coin = fill.get("coin", self.coin)
            price = str(Decimal(str(fill.get("px", mark_px))))
            size = str(Decimal(str(fill.get("sz", "0"))))
            side_raw = fill.get("side", "")
            
            # Map side (same logic as parse_trade for consistency)
            if side_raw.upper() in ["B", "BUY"]:
                side = "LONG"
                order_side = "BUY"
            elif side_raw.upper() in ["A", "S", "SELL"]:
                side = "SHORT"
                order_side = "SELL"
            else:
                side = "UNKNOWN"
                order_side = "UNKNOWN"
            
            # Parse timestamp
            timestamp_ms = fill.get("time")
            if timestamp_ms:
                dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc)
                block_timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            else:
                block_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            
            # Calculate liquidation value
            try:
                liquidation_value_usd = str(Decimal(price) * Decimal(size))
            except:
                liquidation_value_usd = "0"
            
            # Extract fee
            fee = str(Decimal(str(fill.get("fee", "0"))))
            
            # Determine position_side from explicit raw data fields ONLY
            # Default to UNKNOWN - do NOT infer from order_side
            position_side = "UNKNOWN"
            position_side_inferred = False
            
            # Check for explicit position direction fields in raw data
            # Hyperliquid may provide: positionSide, liquidatedSide, szi (signed size), dir, etc.
            
            # Check liquidation info first
            if liquidation_info.get("positionSide"):
                position_side = str(liquidation_info["positionSide"]).upper()
                position_side_inferred = False  # Explicit field
            elif liquidation_info.get("liquidatedSide"):
                position_side = str(liquidation_info["liquidatedSide"]).upper()
                position_side_inferred = False  # Explicit field
            
            # Check fill-level fields
            elif "dir" in fill:
                # Hyperliquid 'dir' field: "Open Long", "Close Long", etc.
                dir_val = str(fill["dir"]).upper()
                if "LONG" in dir_val:
                    position_side = "LONG"
                    position_side_inferred = False  # Explicit field
                elif "SHORT" in dir_val:
                    position_side = "SHORT"
                    position_side_inferred = False  # Explicit field
            
            elif "szi" in fill:
                # Signed size: positive = long, negative = short
                try:
                    szi_val = float(fill["szi"])
                    if szi_val > 0:
                        position_side = "LONG"
                        position_side_inferred = False  # Explicit field
                    elif szi_val < 0:
                        position_side = "SHORT"
                        position_side_inferred = False  # Explicit field
                except:
                    pass
            
            # If no explicit field found, remain UNKNOWN (no inference from order_side)
            
            message = {
                "tx_hash": tx_hash,
                "block_number": 0,
                "block_timestamp": block_timestamp,
                "user_address": liquidated_user or user,
                "coin": coin,
                "side": side,  # Preserved for backward compatibility (ambiguous semantics)
                "size": size,
                "price": price,
                "fee": fee,
                "tx_type": "LIQUIDATION",
                # Extended fields
                "order_side": order_side,  # BUY/SELL - liquidator's order direction
                "position_side": position_side,  # LONG/SHORT/UNKNOWN - liquidated position direction
                "position_side_inferred": position_side_inferred,  # True if inferred from order_side, False if unknown
                "side_semantics": "BACKWARD_COMPAT_AMBIGUOUS",  # Clarify that 'side' field is for compatibility only
                "liquidated_size": size,
                "liquidation_price": price,
                "liquidation_value_usd": liquidation_value_usd,
                "liquidation_method": method,
                "liquidator_address": user if user != liquidated_user else None,
                "mark_price": str(Decimal(str(mark_px))),
                "raw_data": fill
            }
            
            # Remove None values
            message = {k: v for k, v in message.items() if v is not None}
            
            return message
        
        except Exception as e:
            print(f"✗ Error parsing liquidation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_position(self, position: Dict[str, Any], margin_summary: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a position update into schema format
        
        Args:
            position: Asset position data
            margin_summary: Margin summary from clearinghouse state
            raw_data: Complete raw message for reference
            
        Returns:
            Parsed position message
        """
        try:
            # Extract position type and data
            position_data = position.get("position", {})
            
            coin = position_data.get("coin", "UNKNOWN")
            szi = position_data.get("szi", "0")  # Signed size (positive = long, negative = short)
            
            # Determine side based on szi sign
            size_decimal = Decimal(str(szi))
            if size_decimal > 0:
                side = "LONG"
                size = str(abs(size_decimal))
            elif size_decimal < 0:
                side = "SHORT"
                size = str(abs(size_decimal))
            else:
                side = "NONE"
                size = "0"
            
            # Generate unique ID
            user_address = raw_data.get("data", {}).get("user", "UNKNOWN")
            timestamp = datetime.now(timezone.utc)
            block_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            
            id_str = f"{user_address}_{coin}_{timestamp.timestamp()}"
            position_id = "0x" + hashlib.sha256(id_str.encode()).hexdigest()
            
            # Extract position details
            entry_px = position_data.get("entryPx", "0")
            mark_px = position_data.get("markPx", "0")
            leverage = position_data.get("leverage", {})
            unrealized_pnl = position_data.get("unrealizedPnl", "0")
            margin_used = position_data.get("marginUsed", "0")
            
            message = {
                "position_id": position_id,
                "block_timestamp": block_timestamp,
                "user_address": user_address,
                "coin": coin,
                "side": side,
                "size": size,
                "entry_price": str(Decimal(str(entry_px))),
                "mark_price": str(Decimal(str(mark_px))),
                "leverage": str(leverage.get("value", 1)) if isinstance(leverage, dict) else str(leverage),
                "margin": str(Decimal(str(margin_used))),
                "unrealized_pnl": str(Decimal(str(unrealized_pnl))),
                "account_value": str(Decimal(str(margin_summary.get("accountValue", "0")))),
                "tx_type": "POSITION",
                "raw_data": position
            }
            
            return message
        
        except Exception as e:
            print(f"✗ Error parsing position: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_prices(self, mids: Dict[str, str], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse price updates into schema format
        
        Args:
            mids: Dictionary of coin -> mid price
            raw_data: Complete raw message for reference
            
        Returns:
            Parsed price update message
        """
        try:
            timestamp = datetime.now(timezone.utc)
            block_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            
            # Generate unique ID
            id_str = f"prices_{timestamp.timestamp()}"
            price_id = "0x" + hashlib.sha256(id_str.encode()).hexdigest()
            
            # Convert mids to structured format
            price_updates = []
            for coin, mid_price in mids.items():
                price_updates.append({
                    "coin": coin,
                    "price": str(Decimal(str(mid_price)))
                })
            
            message = {
                "price_id": price_id,
                "block_timestamp": block_timestamp,
                "tx_type": "PRICE",
                "prices": price_updates,
                "raw_data": {"mids": mids}
            }
            
            return message
        
        except Exception as e:
            print(f"✗ Error parsing prices: {e}")
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
