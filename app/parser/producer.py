"""
Kafka Producer for sending parsed messages to Kafka
"""
import json
from typing import Dict, Any, Optional

from kafka import KafkaProducer


class MessageProducer:
    """Kafka producer for sending parsed messages"""

    def __init__(self, bootstrap_servers: str, topic: str, dry_run: bool = False):
        self.topic = topic
        self.dry_run = dry_run
        self.producer: Optional[KafkaProducer] = None

        if self.dry_run:
            print("✓ Running in DRY_RUN mode (messages will only be printed)")
            return

        try:
            # 重点：把 max_request_size / request_timeout 调大一点，避免大消息直接失败
            self.producer = KafkaProducer(
                bootstrap_servers=[s.strip() for s in bootstrap_servers.split(",") if s.strip()],
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                acks="all",
                retries=5,
                linger_ms=0,
                request_timeout_ms=30000,
                max_block_ms=30000,
                max_request_size=5 * 1024 * 1024,  # 5MB
                api_version_auto_timeout_ms=30000,
            )
            print(f"✓ Kafka producer initialized: {bootstrap_servers}")
            print(f"✓ Default topic: {topic}")
        except Exception as e:
            print(f"✗ Failed to initialize Kafka producer: {repr(e)}")
            print("  Falling back to DRY_RUN mode")
            self.dry_run = True
            self.producer = None

    def send_message(self, message: Dict[str, Any], topic: Optional[str] = None) -> bool:
        target_topic = topic if topic else self.topic

        try:
            if self.dry_run or not self.producer:
                print(f"\n[DRY_RUN] Would send to topic '{target_topic}'")
                print(json.dumps(message, indent=2, ensure_ascii=False)[:2000])
                return True

            future = self.producer.send(target_topic, value=message)
            record_metadata = future.get(timeout=30)

            # 重点：每次真的发成功都给你一个“强确认”
            print(f"✓ SENT -> {record_metadata.topic}[{record_metadata.partition}] offset={record_metadata.offset}")
            return True

        except Exception as e:
            # 重点：失败必须看得见
            print(f"✗ SEND FAILED -> topic={target_topic}, err={repr(e)}")
            return False

    def flush(self):
        if self.producer and not self.dry_run:
            try:
                self.producer.flush(timeout=30)
            except Exception as e:
                print(f"✗ Flush failed: {repr(e)}")

    def close(self):
        if self.producer and not self.dry_run:
            try:
                self.producer.flush(timeout=30)
                self.producer.close(timeout=30)
            except Exception as e:
                print(f"✗ Close failed: {repr(e)}")
