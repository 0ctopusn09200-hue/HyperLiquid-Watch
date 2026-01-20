"""
Test Kafka Consumer - Verify messages in hyperliquid-raw-trades topic
"""
import os
import json
import signal
import sys
from kafka import KafkaConsumer
from dotenv import load_dotenv


def main():
    """Main test consumer function"""
    load_dotenv()
    
    # Configuration
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "hyperliquid-raw-trades")
    
    print("\n" + "="*60)
    print("Kafka Consumer Test")
    print("="*60)
    print(f"Kafka Servers: {kafka_servers}")
    print(f"Topic: {kafka_topic}")
    print("="*60 + "\n")
    
    # Setup graceful shutdown
    def signal_handler(sig, frame):
        print("\n⚠ Shutting down consumer...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create consumer
        consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_servers.split(","),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True,
            group_id='parser-test-consumer'
        )
        
        print(f"✓ Connected to Kafka, listening for messages...\n")
        
        message_count = 0
        
        # Consume messages
        for message in consumer:
            message_count += 1
            
            print(f"\n{'='*60}")
            print(f"Message #{message_count}")
            print(f"{'='*60}")
            print(f"Topic: {message.topic}")
            print(f"Partition: {message.partition}")
            print(f"Offset: {message.offset}")
            print(f"Timestamp: {message.timestamp}")
            print(f"\nValue:")
            print(json.dumps(message.value, indent=2, ensure_ascii=False))
            print(f"{'='*60}\n")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
