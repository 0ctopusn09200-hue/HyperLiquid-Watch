"""
Configuration management for Backend service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@postgres:5432/hyperliquid"
    
    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_computed_data: str = "hyperliquid.computed_data"
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    api_prefix: str = "/api/v1"
    
    # WebSocket
    ws_path: str = "/api/v1/ws"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
