# app/computer/main.py
import os
import time
import json
import hashlib
import datetime
import traceback
from typing import Any, Dict, Optional

from kafka import KafkaConsumer, KafkaProducer


# -------------------- Config --------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

RAW_TRADES_TOPIC = os.getenv("RAW_TRADES_TOPIC", "hyperliquid-raw-trades")
RAW_PRICE_TOPIC = os.getenv("RAW_PRICE_TOPIC", "hyperliquid-raw-price")

RAW_TOPICS = [RAW_TRADES_TOPIC, RAW_PRICE_TOPIC]

COMPUTED_TOPIC = os.getenv("COMPUTED_TOPIC", "hyperliquid.computed_data")

# 为了先打通 DB：默认阈值很低（1 美元）
LIQ_THRESHOLD_USD = float(os.getenv("LIQ_THRESHOLD_USD", "1"))


# -------------------- Helpers --------------------
def pick(d: Any, *keys: str, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def make_tx_hash(obj: dict) -> str:
    """
    Deterministic unique id for pipeline (NOT real chain tx hash).
    Used for DB ON CONFLICT.
    """
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def utc_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


# -------------------- Main --------------------
def main():
    print("✅ computer main() entered")

    consumer = KafkaConsumer(
        *RAW_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="computer-group",
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"✅ Computer started. RAW={RAW_TOPICS} -> COMPUTED={COMPUTED_TOPIC}")
    print(f"✅ LIQ_THRESHOLD_USD={LIQ_THRESHOLD_USD}")

    for msg in consumer:
        try:
            raw = msg.value or {}
            topic = msg.topic or ""

            # 基础 computed：保持最小计算 + 保留 raw
            computed: Dict[str, Any] = {
                "ts_ms": int(time.time() * 1000),
                "source_topic": topic,
                "coin": None,
                "price": None,
                "size": None,
                "data_type": "UNKNOWN",  # 后面会规范成 PRICE / TRADE / LIQUIDATION
                "raw": raw,              # 保留原始数据
            }

            # -------------------- PRICE topic --------------------
            if "raw-price" in topic:
                # 你的 price raw 里是 tx_type=PRICE + prices 列表
                computed["data_type"] = "PRICE"
                # price 这种消息是批量 prices 列表，不强行拆，交给下游用 raw
                # 这里只做日志友好字段
                computed["coin"] = pick(raw, "coin", "token", "symbol")
                computed["price"] = safe_float(pick(raw, "price", "px", "markPrice"))

            # -------------------- TRADES topic --------------------
            elif "raw-trades" in topic:
                # 根据你提供的真实结构：
                # {"token":"BTC","side":"BUY","price":"67723.0","size":"0.06469","value_usd":"4381.000870","address":"UNKNOWN"}
                computed["data_type"] = "TRADE"

                coin = pick(raw, "token", "coin", "symbol", default="UNKNOWN")
                price = safe_float(pick(raw, "price"))
                size = safe_float(pick(raw, "size"))
                value_usd = safe_float(pick(raw, "value_usd"))
                side = pick(raw, "side", default="unknown")
                user = pick(raw, "address", "user_address", "user", "account")

                computed["coin"] = coin
                computed["price"] = price
                computed["size"] = size

                # 如果 value_usd 不存在，就自己算
                if value_usd is None and price is not None and size is not None:
                    value_usd = abs(price * size)

                # -------------------- MVP liquidation --------------------
                # 先打通链路：把“大额成交”视为 liquidation
                if value_usd is not None and value_usd >= LIQ_THRESHOLD_USD:
                    computed["data_type"] = "LIQUIDATION"

                    bn = int(time.time())

                    # ✅ 顶层放一份：防 backend 从 msg.get("block_number") 取
                    computed["block_number"] = bn

                    # ✅ raw 里也放一份：防 backend 从 msg["raw"].get("block_number") 取
                    if isinstance(computed.get("raw"), dict):
                        computed["raw"]["block_number"] = bn

                    computed["data"] = {
                        "tx_hash": make_tx_hash(raw),
                        "block_timestamp": utc_iso(),
                        "user_address": user,
                        "coin": coin,
                        "side": side,
                        "liquidated_size": abs(size or 0.0),
                        "liquidation_price": price,
                        "liquidation_value_usd": value_usd,
                        "block_number": bn,  # ✅ data 里也放一份
                    }

                else:
                    computed["data"] = {
                        "coin": coin,
                        "side": side,
                        "price": price,
                        "size": size,
                        "value_usd": value_usd,
                        "address": user,
                    }

            # 其他 topic：不处理
            else:
                computed["data_type"] = "UNKNOWN"

            # 发到 computed topic（由 producer 自动批量发送，避免 per-message flush 导致 KafkaTimeoutError）
            producer.send(COMPUTED_TOPIC, computed)

            # 日志：你能一眼看见是否开始出 LIQUIDATION
            if computed.get("data_type") == "LIQUIDATION":
                v = computed.get("data", {}).get("liquidation_value_usd")
                p = computed.get("data", {}).get("liquidation_price")
                c = computed.get("data", {}).get("coin")
                print(f"🔥 sent computed: {topic} LIQUIDATION {c} value_usd={v} price={p}")
            else:
                print(f"➡️ sent computed: {topic} {computed.get('coin')} {computed.get('price')}")

        except Exception:
            print("❌ Error processing message:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
