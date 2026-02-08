# app/computer/main.py
import json
import os
import time
from kafka import KafkaConsumer, KafkaProducer


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

RAW_TOPICS = [
    os.getenv("RAW_TRADES_TOPIC", "hyperliquid-raw-trades"),
    os.getenv("RAW_PRICE_TOPIC", "hyperliquid-raw-price"),
]

COMPUTED_TOPIC = os.getenv("COMPUTED_TOPIC", "hyperliquid.computed_data")


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

    for msg in consumer:
        raw = msg.value

        # 先做“最小计算”：统一字段 + 保留 raw，方便你后续再升级成真正指标
        computed = {
            "ts_ms": int(time.time() * 1000),
            "source_topic": msg.topic,
            "coin": raw.get("coin") or raw.get("symbol"),
            "price": raw.get("price"),
            "size": raw.get("size"),
            "raw": raw,
        }

        producer.send(COMPUTED_TOPIC, computed)
        producer.flush()
        print("➡️ sent computed:", computed.get("source_topic"), computed.get("coin"), computed.get("price"))


if __name__ == "__main__":
    main()
