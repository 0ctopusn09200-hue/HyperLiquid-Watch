"""
Kafka consumer for computed data.
- Consume hyperliquid.computed_data
- Write LIQUIDATION events into Postgres (MVP)
- Broadcast to WebSocket (unchanged)
"""
import json
import asyncio
import threading
import time
import logging
from typing import Optional
from decimal import Decimal
from datetime import datetime

from kafka import KafkaConsumer
import psycopg2
from psycopg2.extras import Json

from config import settings
from websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kafka")


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
        servers = settings.kafka_bootstrap_servers.split(",")

        group_id = f"backend-consumer-debug-{int(time.time())}"

        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group_id,
            request_timeout_ms=30000,
            api_version_auto_timeout_ms=30000,
        )

        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()

        logger.info(f"[Kafka] Consumer started, topic={topic}, group_id={group_id}")

    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()

    def _consume_loop(self):
        logger.info("[Kafka] Consume loop started")
        while self.running:
            records = self.consumer.poll(timeout_ms=1000)
            for _, messages in records.items():
                for msg in messages:
                    logger.info(
                        f"[Kafka] Received {msg.topic} partition={msg.partition} offset={msg.offset}"
                    )
                    if self.main_loop:
                        asyncio.run_coroutine_threadsafe(
                            self._process_message(msg.value),
                            self.main_loop,
                        )
        logger.info("[Kafka] Consume loop exited")

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
    def _insert_liquidation(message: dict):
        data = message.get("data", {}) or {}

        tx_hash = data.get("tx_hash")
        if not tx_hash:
            logger.warning("[DB] Skip liquidation: missing tx_hash")
            return

        block_ts = data.get("block_timestamp") or datetime.utcnow().isoformat() + "Z"

        def dec(v):
            return None if v is None else Decimal(str(v))

        conn = None
        cur = None
        try:
            conn = KafkaConsumerService._get_db_conn()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO liquidations (
                    tx_hash,
                    block_timestamp,
                    user_address,
                    coin,
                    side,
                    liquidated_size,
                    liquidation_value_usd,
                    raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tx_hash) DO NOTHING
                """,
                (
                    tx_hash,
                    block_ts,
                    data.get("user_address"),
                    data.get("coin") or message.get("coin"),
                    data.get("side"),
                    dec(data.get("liquidated_size")),
                    dec(data.get("liquidation_value_usd")),
                    Json(message),
                ),
            )
            conn.commit()
            logger.info(f"[DB] Inserted liquidation tx={tx_hash}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.warning(f"[DB] Insert liquidation failed: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    # -------------------------
    # Message processing
    # -------------------------
    async def _process_message(self, message: dict):
        data_type = message.get("data_type")
        data = message.get("data", {})

        if data_type == "LIQUIDATION":
            # 写 DB（同步逻辑，放到线程池）
            await asyncio.to_thread(self._insert_liquidation, message)

            # WebSocket（保持你原来的）
            from utils.formatters import format_relative_time, truncate_address, format_token_amount

            ts = data.get("block_timestamp")
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()

            size = Decimal(str(data.get("liquidated_size", 0)))

            activity_data = {
                "time": format_relative_time(ts),
                "address": truncate_address(data.get("user_address", "")),
                "token": data.get("coin", "N/A"),
                "value": float(data.get("liquidation_value_usd", 0)),
                "side": "Long" if data.get("side", "").upper() in ["LONG", "L"] else "Short",
                "type": "Close",
                "amount": format_token_amount(size, data.get("coin", "N/A")),
                "timestamp": ts.isoformat() + "Z",
                "txHash": data.get("tx_hash"),
            }

            await manager.broadcast_whale_activity(activity_data)


kafka_consumer = KafkaConsumerService()
