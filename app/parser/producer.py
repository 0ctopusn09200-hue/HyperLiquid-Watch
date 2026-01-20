"""
Kafka Producer for sending parsed messages to Kafka
"""
import json
import os
from kafka import KafkaProducer
from typing import Dict, Any, Optional


class MessageProducer:
    """Kafka producer for sending parsed trade messages"""
    
    def __init__(self, bootstrap_servers: str, topic: str, dry_run: bool = False):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker addresses (comma-separated)
            topic: Kafka topic name
            dry_run: If True, only print messages without sending to Kafka
        """
        self.topic = topic
        self.dry_run = dry_run
        self.producer: Optional[KafkaProducer] = None
        
        if not dry_run:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
                print(f"✓ Kafka producer initialized: {bootstrap_servers}")
                print(f"✓ Target topic: {topic}")
            except Exception as e:
                print(f"✗ Failed to initialize Kafka producer: {e}")
                print("  Falling back to DRY_RUN mode")
                self.dry_run = True
        else:
            print("✓ Running in DRY_RUN mode (messages will only be printed)")
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to Kafka or print it in dry-run mode
        
        Args:
            message: Message dict to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.dry_run:
                print(f"\n[DRY_RUN] Would send to topic '{self.topic}':")
                print(json.dumps(message, indent=2, ensure_ascii=False))
                return True
            
            if self.producer:
                future = self.producer.send(self.topic, message)
                # Wait for send to complete
                record_metadata = future.get(timeout=10)
                print(f"✓ Sent message to {record_metadata.topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
                return True
            else:
                print("✗ Producer not initialized")
                return False
                
        except Exception as e:
            print(f"✗ Error sending message: {e}")
            return False
    
    def flush(self):
        """Flush any pending messages"""
        if self.producer and not self.dry_run:
            try:
                self.producer.flush(timeout=10)
                print("✓ All messages flushed")
            except Exception as e:
                print(f"✗ Error flushing messages: {e}")
    
    def close(self):
        """Close the producer gracefully"""
        if self.producer and not self.dry_run:
            try:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
                print("✓ Kafka producer closed")
            except Exception as e:
                print(f"✗ Error closing producer: {e}")
