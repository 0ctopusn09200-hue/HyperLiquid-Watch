"""
Configuration management for Backend service
"""
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import urlparse


class Settings(BaseSettings):
    """Application settings"""

    # =========================
    # Database (single source)
    # =========================
    database_url: str = "postgresql://postgres:postgres@postgres:5432/hyperliquid"

    # --- Derived Postgres fields (for psycopg2 etc.) ---
    @property
    def postgres_host(self) -> str:
        return urlparse(self.database_url).hostname or "postgres"

    @property
    def postgres_port(self) -> int:
        return urlparse(self.database_url).port or 5432

    @property
    def postgres_db(self) -> str:
        return (urlparse(self.database_url).path or "/hyperliquid").lstrip("/")

    @property
    def postgres_user(self) -> str:
        return urlparse(self.database_url).username or "postgres"

    @property
    def postgres_password(self) -> str:
        return urlparse(self.database_url).password or "postgres"

    # =========================
    # Kafka
    # =========================
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_computed_data: str = "hyperliquid.computed_data"

    # =========================
    # Server
    # =========================
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    api_prefix: str = "/api/v1"

    # =========================
    # WebSocket
    # =========================
    ws_path: str = "/api/v1/ws"

    # =========================
    # Logging
    # =========================
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
