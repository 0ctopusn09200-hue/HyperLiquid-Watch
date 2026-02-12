"""
Kafka consumer for computed data.
FINAL STABLE VERSION (NO CIRCULAR JSON)
- Consume hyperliquid.computed_data
- Write LIQUIDATION events into Postgres
- Broadcast to WebSocket
"""

import json
import asyncio
import threading
import time
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import psycopg2
from psycopg2.extras import Json

from config import settings
from websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kafka")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_safe(obj: Any) -> Any:
    """
    Make obj JSON-serializable safely (and break potential cycles by re-encoding).
    - default=str: convert Decimal/datetime/etc.
    - loads(dumps()): ensures pure JSON types, and removes any hidden refs
    """
    try:
        return json.loads(json.dumps(obj, ensure_ascii=False, default=str))
    except Exception:
        # fallback: last resort
        return {"_unserializable": str(obj)}


class KafkaConsumerService:
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None

    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        self.main_loop = loop

    # -------------------------
    # Kafka
    # -------------------------
    def start(self):
        if self.running:
            return

        topic = settings.kafka_topic_computed_data
        servers = [s.strip() for s in settings.kafka_bootstrap_servers.split(",") if s.strip()]
        group_id = f"backend-consumer-{int(time.time())}"

        max_retries = 12
        retry_delay = 5

        for attempt in range(1, max_retries + 1):
            try:
                self.consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=servers,
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    group_id=group_id,
                )
                break
            except NoBrokersAvailable as e:
                if attempt < max_retries:
                    logger.warning(
                        f"[Kafka] Attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {retry_delay}s (Kafka may still be starting)..."
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[Kafka] All {max_retries} attempts failed. Giving up.")
                    raise

        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()

        logger.info(f"[Kafka] Consumer started topic={topic} group_id={group_id} servers={servers}")

    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()

    def _safe_deserialize(self, raw: bytes) -> Optional[Dict[str, Any]]:
        """Deserialize message, skip invalid JSON to avoid crashing the consume loop."""
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(
                f"[Kafka] Skip malformed message: {e}. "
                f"Raw preview: {raw[:200]!r}"
            )
            return None

    def _consume_loop(self):
        logger.info("[Kafka] Consume loop started")
        while self.running:
            records = self.consumer.poll(timeout_ms=1000)
            for _, messages in records.items():
                for msg in messages:
                    value = self._safe_deserialize(msg.value) if msg.value else None
                    if value is not None and self.main_loop:
                        asyncio.run_coroutine_threadsafe(self._process_message(value), self.main_loop)

    # -------------------------
    # Normalization (NO CIRCULAR _raw)
    # -------------------------
    @staticmethod
    def _normalize_message(message: Dict[str, Any]) -> Dict[str, Any]:
        # Make a safe raw snapshot FIRST (do NOT reference itself)
        raw_snapshot = _json_safe(message)

        if not isinstance(message, dict):
            return {"data_type": "UNKNOWN", "coin": None, "data": {}, "_raw": raw_snapshot}

        # If already normalized, DO NOT do message["_raw"] = message  (that creates self-reference)
        # Instead, keep a safe raw snapshot.
        if "data_type" in message and isinstance(message.get("data"), dict):
            coin = message.get("coin") or message["data"].get("coin") or message["data"].get("token")
            return {
                "data_type": str(message.get("data_type") or "UNKNOWN").upper(),
                "coin": coin,
                "data": message.get("data") or {},
                "_raw": raw_snapshot,
            }

        # Otherwise, try to pick data object
        data_obj = None
        if isinstance(message.get("data"), dict):
            data_obj = message["data"]
        elif isinstance(message.get("raw"), dict):
            data_obj = message["raw"]
        else:
            data_obj = message

        # Detect type
        data_type = (
            message.get("data_type")
            or message.get("tx_type")
            or (data_obj.get("tx_type") if isinstance(data_obj, dict) else None)
            or (data_obj.get("type") if isinstance(data_obj, dict) else None)
            or "UNKNOWN"
        )

        coin = None
        if isinstance(data_obj, dict):
            coin = data_obj.get("coin") or data_obj.get("token")
        if not coin:
            coin = message.get("coin")

        return {
            "data_type": str(data_type).upper(),
            "coin": coin,
            "data": data_obj if isinstance(data_obj, dict) else {},
            "_raw": raw_snapshot,
        }

    @staticmethod
    def _is_liquidation(normalized: Dict[str, Any]) -> bool:
        dt = (normalized.get("data_type") or "").upper()
        if dt == "LIQUIDATION":
            return True
        data = normalized.get("data", {}) or {}
        inner = (data.get("tx_type") or data.get("type") or "").upper()
        return inner == "LIQUIDATION"

    # -------------------------
    # DB helpers
    # -------------------------
    @staticmethod
    def _get_db_conn():
        return psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )

    @staticmethod
    def _pick_first(d: Dict[str, Any], keys):
        if not isinstance(d, dict):
            return None
        for k in keys:
            v = d.get(k)
            if v not in (None, ""):
                return v
        return None

    @staticmethod
    def _dec(v):
        return None if v is None else Decimal(str(v))

    @staticmethod
    def _insert_liquidation(normalized: Dict[str, Any]):
        data = normalized.get("data", {}) or {}
        raw = normalized.get("_raw", {}) or {}

        # tx_hash (support tx_hash/txHash, also raw nested)
        tx_hash = (
            KafkaConsumerService._pick_first(data, ["tx_hash", "txHash", "hash"])
            or KafkaConsumerService._pick_first(raw, ["tx_hash", "txHash", "hash"])
        )
        if not tx_hash:
            logger.warning("[DB] Skip liquidation: missing tx_hash")
            return

        # block_timestamp
        block_ts = (
            KafkaConsumerService._pick_first(data, ["block_timestamp", "timestamp"])
            or KafkaConsumerService._pick_first(raw, ["block_timestamp", "timestamp"])
            or _now_utc_iso()
        )

        # block_number (NOT NULL in your table)
        block_number = (
            KafkaConsumerService._pick_first(data, ["block_number"])
            or KafkaConsumerService._pick_first(raw, ["block_number"])
        )
        if block_number is None:
            block_number = int(time.time())

        # liquidation_price (NOT NULL in your table)
        liquidation_price = KafkaConsumerService._pick_first(data, ["liquidation_price", "price"])
        if liquidation_price is None:
            liquidation_price = KafkaConsumerService._pick_first(raw, ["liquidation_price", "price"])
        if liquidation_price is None:
            logger.warning(f"[DB] Skip liquidation: missing liquidation_price tx={tx_hash}")
            return

        # other fields
        user_address = KafkaConsumerService._pick_first(data, ["user_address", "address"]) or "UNKNOWN"
        coin = KafkaConsumerService._pick_first(data, ["coin", "token"]) or normalized.get("coin") or "UNKNOWN"
        side = KafkaConsumerService._pick_first(data, ["side"]) or KafkaConsumerService._pick_first(raw, ["side"])

        liquidated_size = KafkaConsumerService._pick_first(data, ["liquidated_size", "size"])
        liquidation_value_usd = KafkaConsumerService._pick_first(data, ["liquidation_value_usd", "value_usd"])

        # raw_data MUST be json-safe and non-circular
        raw_data = _json_safe(raw)

        try:
            conn = KafkaConsumerService._get_db_conn()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO liquidations (
                    tx_hash,
                    block_number,
                    block_timestamp,
                    user_address,
                    coin,
                    side,
                    liquidated_size,
                    liquidation_price,
                    liquidation_value_usd,
                    raw_data
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (tx_hash) DO NOTHING
                """,
                (
                    tx_hash,
                    int(block_number),
                    block_ts,
                    user_address,
                    coin,
                    side,
                    KafkaConsumerService._dec(liquidated_size),
                    KafkaConsumerService._dec(liquidation_price),
                    KafkaConsumerService._dec(liquidation_value_usd),
                    Json(raw_data),
                ),
            )

            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"[DB] Inserted liquidation tx={tx_hash}")

        except Exception as e:
            logger.warning(f"[DB] Insert liquidation failed: {e}")

    # -------------------------
    # Message processing
    # -------------------------
    async def _process_message(self, message: dict):
        normalized = self._normalize_message(message)

        if not self._is_liquidation(normalized):
            return

        await asyncio.to_thread(self._insert_liquidation, normalized)

        # WebSocket broadcast
        data = normalized.get("data", {}) or {}
        activity = {
            "token": data.get("coin", normalized.get("coin") or "N/A"),
            "value": float(data.get("liquidation_value_usd", data.get("value_usd", 0)) or 0),
            "side": data.get("side", "Unknown"),
            "timestamp": data.get("block_timestamp") or data.get("timestamp") or _now_utc_iso(),
            "txHash": data.get("tx_hash") or data.get("txHash"),
        }
        await manager.broadcast_whale_activity(activity)
        
        # Broadcast price update (so frontend heatmap/current price can update in real-time)
        try:
            price = data.get("liquidation_price") or data.get("price")
            if price is not None:
                price_data = {
                    "token": activity["token"],
                    "price": float(price),
                    "timestamp": activity["timestamp"],
                }
                await manager.broadcast_price_update(price_data)
        except Exception as e:
            logger.warning(f"[Kafka] Failed to broadcast price update: {e}")

        # Compute and broadcast short-term long/short ratio for this token (last 5 minutes)
        try:
            conn = KafkaConsumerService._get_db_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                  SUM(CASE WHEN UPPER(side)='SELL' THEN COALESCE(liquidation_value_usd,0) ELSE 0 END) AS long_v,
                  SUM(CASE WHEN UPPER(side)='BUY' THEN COALESCE(liquidation_value_usd,0) ELSE 0 END) AS short_v
                FROM liquidations
                WHERE coin = %s
                  AND block_timestamp >= (NOW() - INTERVAL '300 seconds')
                """,
                (activity["token"],),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                long_v = float(row[0] or 0)
                short_v = float(row[1] or 0)
                total = long_v + short_v
                long_pct = (long_v / total * 100) if total > 0 else 50.0
                short_pct = (short_v / total * 100) if total > 0 else 50.0

                ratio_payload = {
                    "token": activity["token"],
                    "longPercent": round(long_pct, 2),
                    "shortPercent": round(short_pct, 2),
                    "longVolume": long_v,
                    "shortVolume": short_v,
                    "timestamp": _now_utc_iso(),
                }
                await manager.broadcast_long_short_ratio(ratio_payload)
        except Exception as e:
            logger.warning(f"[Kafka] Failed to compute/broadcast ratio: {e}")


kafka_consumer = KafkaConsumerService()
