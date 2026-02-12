"""
Parser Service - Hyperliquid WebSocket to Kafka
"""
import asyncio
import os
import signal
import sys
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from hl_ws_client import HyperliquidWSClient
from producer import MessageProducer


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"


class ParserService:
    def __init__(self):
        load_dotenv()

        self.coin = os.getenv("HL_COIN", "BTC")

        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.kafka_topic_trades = os.getenv("KAFKA_TOPIC", "hyperliquid-raw-trades")
        self.kafka_topic_prices = os.getenv("KAFKA_TOPIC_PRICES", "hyperliquid-raw-price")

        self.dry_run = os.getenv("DRY_RUN", "0") == "1"

        self.enable_price_feed = os.getenv("ENABLE_PRICE_FEED", "false").lower() == "true"
        self.enable_trade_feed = os.getenv("ENABLE_TRADE_FEED", "true").lower() == "true"

        # 重点：把大 price 消息分批
        self.price_batch_size = int(os.getenv("PRICE_BATCH_SIZE", "120"))

        # 重点：默认不带 raw_data（否则太肥）
        self.include_raw_data = os.getenv("INCLUDE_RAW_DATA", "false").lower() == "true"

        self.producer = MessageProducer(
            bootstrap_servers=self.kafka_servers,
            topic=self.kafka_topic_trades,
            dry_run=self.dry_run,
        )

        subs = []
        if self.enable_trade_feed:
            subs.append({"type": "trades", "coin": self.coin})
        if self.enable_price_feed:
            subs.append({"type": "allMids"})

        self.ws_client = HyperliquidWSClient(
            coin=self.coin,
            on_message_callback=self.handle_message,
            subscriptions=subs,
        )

        self.running = False

        self._seen = set()
        self._seen_q = deque(maxlen=50000)

        print("\n" + "=" * 60)
        print("Hyperliquid Parser Service")
        print("=" * 60)
        print(f"Coin: {self.coin}")
        print(f"Kafka: {self.kafka_servers}")
        print(f"Trades topic: {self.kafka_topic_trades}")
        print(f"Prices topic: {self.kafka_topic_prices}")
        print(f"ENABLE_TRADE_FEED: {self.enable_trade_feed}")
        print(f"ENABLE_PRICE_FEED: {self.enable_price_feed}")
        print(f"PRICE_BATCH_SIZE: {self.price_batch_size}")
        print(f"INCLUDE_RAW_DATA: {self.include_raw_data}")
        print(f"DRY_RUN: {self.dry_run}")
        print("=" * 60 + "\n")

    async def handle_message(self, data: Dict[str, Any]):
        try:
            channel = data.get("channel")
            if channel == "trades" and self.enable_trade_feed:
                await self._handle_trades(data)
            elif channel == "allMids" and self.enable_price_feed:
                await self._handle_prices(data)
        except Exception as e:
            print(f"✗ Error handling message: {repr(e)}")

    async def _handle_trades(self, data: Dict[str, Any]):
        trades_data = data.get("data", [])
        if not isinstance(trades_data, list):
            return

        for trade in trades_data:
            msg = self.parse_trade(trade)
            if not msg:
                continue

            txh = msg["tx_hash"]
            if txh in self._seen:
                continue
            self._seen.add(txh)
            self._seen_q.append(txh)
            if len(self._seen_q) == self._seen_q.maxlen:
                self._seen = set(self._seen_q)

            ok = self.producer.send_message(msg, topic=self.kafka_topic_trades)
            if not ok:
                # 失败就别悄悄过去
                print("✗ Trade send failed (see error above)")

    def parse_trade(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            trade_str = json.dumps(trade, sort_keys=True)
            tx_hash = "0x" + hashlib.sha256(trade_str.encode()).hexdigest()

            price_raw = trade.get("px", trade.get("price"))
            size_raw = trade.get("sz", trade.get("size"))
            side_raw = str(trade.get("side", "")).upper()
            timestamp_ms = trade.get("time")

            if price_raw is None or size_raw is None or not side_raw:
                return None

            price_dec = Decimal(str(price_raw))
            size_dec = Decimal(str(size_raw))
            if price_dec <= 0 or size_dec <= 0:
                return None

            if side_raw in ["B", "BUY"]:
                side = "BUY"
            elif side_raw in ["A", "S", "SELL"]:
                side = "SELL"
            else:
                return None

            if timestamp_ms:
                try:
                    dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc)
                    timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                except Exception:
                    timestamp = utc_ts()
            else:
                timestamp = utc_ts()

            address = trade.get("user") or trade.get("address") or "UNKNOWN"

            msg = {
                "tx_hash": tx_hash,
                "timestamp": timestamp,
                "token": trade.get("coin", self.coin),
                "side": side,
                "price": format(price_dec, "f"),
                "size": format(size_dec, "f"),
                "value_usd": format(price_dec * size_dec, "f"),
                "address": address,
            }

            return msg
        except Exception as e:
            print(f"✗ parse_trade failed: {repr(e)}")
            return None

    async def _handle_prices(self, data: Dict[str, Any]):
        mids_data = data.get("data", {})
        mids = mids_data.get("mids", {})
        if not isinstance(mids, dict):
            return

        # ✅ 分批发送，避免消息过大
        items = list(mids.items())
        total = len(items)
        ts = utc_ts()

        batch = []
        for i, (coin, mid) in enumerate(items, start=1):
            batch.append({"coin": coin, "price": str(Decimal(str(mid)))})
            if len(batch) >= self.price_batch_size or i == total:
                msg = {
                    "price_id": "0x" + hashlib.sha256(f"prices_{ts}_{i}".encode()).hexdigest(),
                    "block_timestamp": ts,
                    "tx_type": "PRICE",
                    "batch_index": (i - 1) // self.price_batch_size,
                    "batch_size": len(batch),
                    "total_coins": total,
                    "prices": batch,
                }
                if self.include_raw_data:
                    msg["raw_data"] = {"mids": mids}  # 不建议开

                ok = self.producer.send_message(msg, topic=self.kafka_topic_prices)
                if not ok:
                    print("✗ Price batch send failed (see error above)")
                    return

                batch = []

    async def start(self):
        self.running = True

        def signal_handler(sig, frame):
            print("\n⚠ Shutdown signal received, stopping...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            print("▶ Starting parser service...")
            await self.ws_client.connect()
        except Exception as e:
            print(f"✗ Fatal error: {repr(e)}")
            await self.stop()

    async def stop(self):
        if not self.running:
            return
        self.running = False
        await self.ws_client.close()
        self.producer.flush()
        self.producer.close()
        print("✓ Parser stopped")
        sys.exit(0)


async def main():
    s = ParserService()
    await s.start()


if __name__ == "__main__":
    asyncio.run(main())
