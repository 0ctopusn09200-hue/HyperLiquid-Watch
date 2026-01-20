"""
Service layer for liquidation map operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import LiquidationMap
from schemas import LiquidationMapResponse, PriceLevelResponse


def get_liquidation_map(
    db: Session,
    coin: str,
    timestamp: Optional[datetime] = None,
    price_min: Optional[Decimal] = None,
    price_max: Optional[Decimal] = None
) -> LiquidationMapResponse:
    """Get liquidation map for a specific coin"""
    query = db.query(LiquidationMap).filter(LiquidationMap.coin == coin)
    
    # Use latest timestamp if not specified
    if timestamp is None:
        latest = db.query(LiquidationMap.timestamp).filter(
            LiquidationMap.coin == coin
        ).order_by(desc(LiquidationMap.timestamp)).first()
        
        if latest:
            timestamp = latest.timestamp
            query = query.filter(LiquidationMap.timestamp == timestamp)
        else:
            return LiquidationMapResponse(coin=coin, timestamp=datetime.utcnow(), price_levels=[])
    else:
        query = query.filter(LiquidationMap.timestamp == timestamp)
    
    # Filter by price range if provided
    if price_min:
        query = query.filter(LiquidationMap.price_level >= price_min)
    if price_max:
        query = query.filter(LiquidationMap.price_level <= price_max)
    
    price_levels = query.order_by(LiquidationMap.price_level).all()
    
    return LiquidationMapResponse(
        coin=coin,
        timestamp=timestamp,
        price_levels=[
            PriceLevelResponse(
                price=level.price_level,
                long_liquidation_value=level.long_liquidation_value,
                short_liquidation_value=level.short_liquidation_value,
                long_liquidation_count=level.long_liquidation_count,
                short_liquidation_count=level.short_liquidation_count
            )
            for level in price_levels
        ]
    )
