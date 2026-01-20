"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ========== Common Schemas ==========

class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiResponse(BaseModel):
    """Standard API response format"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class PaginatedResponse(BaseModel):
    """Paginated response format"""
    code: int = 200
    message: str = "success"
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ========== Liquidation Schemas ==========

class LiquidationResponse(BaseModel):
    """Liquidation event response"""
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
    """Liquidation statistics response"""
    total_liquidations: int
    total_liquidation_value_usd: Decimal
    long_liquidations: int
    long_liquidation_value_usd: Decimal
    short_liquidations: int
    short_liquidation_value_usd: Decimal
    by_coin: dict


# ========== Long/Short Ratio Schemas ==========

class LongShortRatioResponse(BaseModel):
    """Long/Short ratio response"""
    coin: str
    timestamp: datetime
    long_ratio: Decimal
    short_ratio: Decimal
    long_position_value: Decimal
    short_position_value: Decimal
    total_position_value: Decimal
    long_accounts: int
    short_accounts: int

    class Config:
        from_attributes = True


# ========== Liquidation Map Schemas ==========

class PriceLevelResponse(BaseModel):
    """Price level in liquidation map"""
    price: Decimal
    long_liquidation_value: Decimal
    short_liquidation_value: Decimal
    long_liquidation_count: int
    short_liquidation_count: int


class LiquidationMapResponse(BaseModel):
    """Liquidation map response"""
    coin: str
    timestamp: datetime
    price_levels: List[PriceLevelResponse]


# ========== Transaction Schemas ==========

class TransactionResponse(BaseModel):
    """Transaction response"""
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
    raw_data: Optional[dict] = None

    class Config:
        from_attributes = True


# ========== Whale Schemas ==========

class WhaleWatchResponse(BaseModel):
    """Whale watch response"""
    id: int
    wallet_address: str
    alias: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WhaleWatchCreate(BaseModel):
    """Create whale watch request"""
    wallet_address: str
    alias: Optional[str] = None
    description: Optional[str] = None


class WhaleActivityResponse(BaseModel):
    """Whale activity response"""
    id: int
    whale_id: Optional[int] = None
    wallet_address: str
    activity_type: str
    tx_hash: str
    coin: Optional[str] = None
    size: Optional[Decimal] = None
    value_usd: Optional[Decimal] = None
    timestamp: datetime
    details: Optional[dict] = None

    class Config:
        from_attributes = True
