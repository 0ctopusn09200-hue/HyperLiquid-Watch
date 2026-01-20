"""
Parser Service - Hyperliquid WebSocket to Kafka

This package provides a parser service that subscribes to Hyperliquid WebSocket
trades and publishes parsed messages to Kafka.

Main components:
- main.py: Entry point and orchestration
- hl_ws_client.py: Hyperliquid WebSocket client
- producer.py: Kafka producer wrapper
- consumer_test.py: Test consumer for verification
"""

__version__ = "1.0.0"
__author__ = "zhang_yunan"
