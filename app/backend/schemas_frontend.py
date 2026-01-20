"""
Frontend-compatible schemas matching TypeScript interfaces
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal


# ========== Liquidation Heatmap Types ==========

class LiquidationPoint(BaseModel):
    """Price level in liquidation heatmap"""
    price: float
    longVol: float  # Will be multiplied by 10000 for USD display
    shortVol: float  # Will be multiplied by 10000 for USD display
    current: Optional[bool] = False


class LiquidationHeatmapResponse(BaseModel):
    """Liquidation heatmap response"""
    token: str
    currentPrice: float
    points: List[LiquidationPoint]
    minPrice: float
    maxPrice: float


# ========== Long/Short Ratio Types ==========

class LongShortRatioResponse(BaseModel):
    """Long/Short ratio response (frontend format)"""
    longPercent: float  # 0-100
    shortPercent: float  # 0-100
    longVolume: float  # USD
    shortVolume: float  # USD
    longChange24h: float  # percentage change
    shortChange24h: float  # percentage change
    updatedAt: str  # ISO 8601


# ========== Whale Activities Types ==========

PositionSide = Literal["Long", "Short"]
PositionType = Literal["Open", "Close"]


class WhaleTransaction(BaseModel):
    """Whale transaction response"""
    time: str  # Relative time string (e.g., "2 min ago") or ISO timestamp
    address: str  # Wallet address (full or truncated)
    token: str  # Token symbol
    value: float  # USD value
    side: PositionSide
    type: PositionType
    amount: str  # Formatted string (e.g., "28.40572 BTC")
    timestamp: Optional[str] = None  # ISO 8601 for sorting
    txHash: Optional[str] = None  # Transaction hash


class WhaleActivitiesResponse(BaseModel):
    """Whale activities response"""
    transactions: List[WhaleTransaction]
    totalCount: int
    updatedAt: str


# ========== Wallet Position Distribution Types ==========

Sentiment = Literal["bullish", "bearish", "neutral"]


class WalletPositionBucket(BaseModel):
    """Position bucket in distribution"""
    positionSize: str  # e.g., "$0 - $250"
    category: str  # e.g., "Shrimp"
    categoryEn: str  # English category name
    walletCount: int
    openInterestPercent: float
    longValue: str  # Formatted string (e.g., "$717M")
    shortValue: str  # Formatted string (e.g., "$181M")
    longPercent: float  # 0-100
    profitUsers: int
    lossUsers: int
    sentiment: Sentiment


class WalletPositionDistributionResponse(BaseModel):
    """Wallet position distribution response"""
    buckets: List[WalletPositionBucket]
    totalWallets: int
    updatedAt: str


# ========== Error Types ==========

class ApiError(BaseModel):
    """API error response"""
    error: str
    message: str
    statusCode: int
    timestamp: str
