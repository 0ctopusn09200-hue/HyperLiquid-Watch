"""
Pydantic schemas for request/response validation
FINAL — compatible with Plan A realtime ratios
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ========== Common Schemas ==========

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=_utc_iso)


class PaginatedResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=_utc_iso)


# ========== Liquidation Schemas ==========

class LiquidationResponse(BaseModel):
    tx_hash: str
    block_number: int
    block_timestamp: datetime
    user_address: str
    coin: str
    side: str
    liquidated_size: Decimal
    liquidation_price: Decimal
    liquidation_value_usd: Optional[Decimal] = None
    leverage: Optional[Decimal] = None
    margin: Optional[Decimal] = None
    liquidator_address: Optional[str] = None

    class Config:
        from_attributes = True


class LiquidationStatsResponse(BaseModel):
    total_liquidations: int
    total_liquidation_value_usd: Decimal
    long_liquidations: int
    long_liquidation_value_usd: Decimal
    short_liquidations: int
    short_liquidation_value_usd: Decimal
    by_coin: Dict[str, Any]


# ========== Long/Short Ratio Schemas (Plan A realtime) ==========

class LongShortRatioResponse(BaseModel):
    """
    Must match ratio_service.py output (Plan A):
    coin, timestamp, long_ratio, short_ratio, long_short_ratio
    """
    coin: str
    timestamp: datetime
    long_ratio: float
    short_ratio: float
    long_short_ratio: float

    class Config:
        from_attributes = True


# ========== Liquidation Map Schemas ==========

class PriceLevelResponse(BaseModel):
    price: Decimal
    long_liquidation_value: Decimal
    short_liquidation_value: Decimal
    long_liquidation_count: int
    short_liquidation_count: int


class LiquidationMapResponse(BaseModel):
    coin: str
    timestamp: datetime
    price_levels: List[PriceLevelResponse]


# ========== Transaction Schemas ==========

class TransactionResponse(BaseModel):
    tx_hash: str
    block_number: int
    block_timestamp: datetime
    user_address: str
    coin: str
    side: str
    size: Decimal
    price: Decimal
    leverage: Optional[Decimal] = None
    margin: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    tx_type: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ========== Whale Schemas ==========

class WhaleWatchResponse(BaseModel):
    id: int
    wallet_address: str
    alias: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WhaleWatchCreate(BaseModel):
    wallet_address: str
    alias: Optional[str] = None
    description: Optional[str] = None


class WhaleActivityResponse(BaseModel):
    id: int
    whale_id: Optional[int] = None
    wallet_address: str
    activity_type: str
    tx_hash: str
    coin: Optional[str] = None
    size: Optional[Decimal] = None
    value_usd: Optional[Decimal] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
