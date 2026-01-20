"""
SQLAlchemy models matching the database schema
"""
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from database import Base


class Transaction(Base):
    """Transactions table model"""
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    user_address = Column(String(42), nullable=False, index=True)
    coin = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False, index=True)
    size = Column(Numeric(30, 8), nullable=False)
    price = Column(Numeric(30, 8), nullable=False)
    leverage = Column(Numeric(5, 2))
    margin = Column(Numeric(30, 8))
    fee = Column(Numeric(30, 8))
    tx_type = Column(String(50), index=True)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Liquidation(Base):
    """Liquidations table model"""
    __tablename__ = "liquidations"

    id = Column(BigInteger, primary_key=True, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False)
    block_number = Column(BigInteger, nullable=False)
    block_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    user_address = Column(String(42), nullable=False, index=True)
    coin = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False, index=True)
    liquidated_size = Column(Numeric(30, 8), nullable=False)
    liquidation_price = Column(Numeric(30, 8), nullable=False)
    liquidation_value_usd = Column(Numeric(30, 8))
    leverage = Column(Numeric(5, 2))
    margin = Column(Numeric(30, 8))
    liquidator_address = Column(String(42))
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LongShortRatio(Base):
    """Long/Short ratios table model"""
    __tablename__ = "long_short_ratios"

    id = Column(BigInteger, primary_key=True, index=True)
    coin = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    long_ratio = Column(Numeric(10, 4), nullable=False)
    short_ratio = Column(Numeric(10, 4), nullable=False)
    long_position_value = Column(Numeric(30, 8), nullable=False)
    short_position_value = Column(Numeric(30, 8), nullable=False)
    total_position_value = Column(Numeric(30, 8), nullable=False)
    long_accounts = Column(Integer, default=0)
    short_accounts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiquidationMap(Base):
    """Liquidation map table model"""
    __tablename__ = "liquidation_map"

    id = Column(BigInteger, primary_key=True, index=True)
    coin = Column(String(20), nullable=False, index=True)
    price_level = Column(Numeric(30, 8), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    long_liquidation_value = Column(Numeric(30, 8), default=0)
    short_liquidation_value = Column(Numeric(30, 8), default=0)
    long_liquidation_count = Column(Integer, default=0)
    short_liquidation_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Position(Base):
    """Positions table model"""
    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_address = Column(String(42), nullable=False, index=True)
    coin = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    size = Column(Numeric(30, 8), nullable=False)
    entry_price = Column(Numeric(30, 8), nullable=False)
    mark_price = Column(Numeric(30, 8), nullable=False)
    leverage = Column(Numeric(5, 2))
    margin = Column(Numeric(30, 8))
    unrealized_pnl = Column(Numeric(30, 8))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WhaleWatch(Base):
    """Whale watches table model"""
    __tablename__ = "whale_watches"

    id = Column(BigInteger, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    alias = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WhaleActivity(Base):
    """Whale activities table model"""
    __tablename__ = "whale_activities"

    id = Column(BigInteger, primary_key=True, index=True)
    whale_id = Column(BigInteger, ForeignKey("whale_watches.id"), index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    tx_hash = Column(String(66), nullable=False)
    coin = Column(String(20))
    size = Column(Numeric(30, 8))
    value_usd = Column(Numeric(30, 8))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
