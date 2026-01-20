"""
Service layer for liquidation-related operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime
from models import Liquidation
from schemas import LiquidationResponse, LiquidationStatsResponse


def get_recent_liquidations(
    db: Session,
    coin: Optional[str] = None,
    side: Optional[str] = None,
    limit: int = 20
) -> List[LiquidationResponse]:
    """Get recent liquidation events"""
    query = db.query(Liquidation)
    
    if coin:
        query = query.filter(Liquidation.coin == coin)
    if side:
        query = query.filter(Liquidation.side == side)
    
    liquidations = query.order_by(Liquidation.block_timestamp.desc()).limit(limit).all()
    
    return [LiquidationResponse.model_validate(liq) for liq in liquidations]


def get_liquidations(
    db: Session,
    coin: Optional[str] = None,
    side: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[LiquidationResponse], int]:
    """Get liquidations with pagination"""
    query = db.query(Liquidation)
    
    if coin:
        query = query.filter(Liquidation.coin == coin)
    if side:
        query = query.filter(Liquidation.side == side)
    if start_time:
        query = query.filter(Liquidation.block_timestamp >= start_time)
    if end_time:
        query = query.filter(Liquidation.block_timestamp <= end_time)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    liquidations = query.order_by(Liquidation.block_timestamp.desc()).offset(offset).limit(page_size).all()
    
    return [LiquidationResponse.model_validate(liq) for liq in liquidations], total


def get_liquidation_stats(
    db: Session,
    coin: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> LiquidationStatsResponse:
    """Get liquidation statistics"""
    query = db.query(Liquidation)
    
    if coin:
        query = query.filter(Liquidation.coin == coin)
    if start_time:
        query = query.filter(Liquidation.block_timestamp >= start_time)
    if end_time:
        query = query.filter(Liquidation.block_timestamp <= end_time)
    
    # Total stats
    total_count = query.count()
    total_value = query.with_entities(func.sum(Liquidation.liquidation_value_usd)).scalar() or 0
    
    # Long stats
    long_query = query.filter(Liquidation.side == "LONG")
    long_count = long_query.count()
    long_value = long_query.with_entities(func.sum(Liquidation.liquidation_value_usd)).scalar() or 0
    
    # Short stats
    short_query = query.filter(Liquidation.side == "SHORT")
    short_count = short_query.count()
    short_value = short_query.with_entities(func.sum(Liquidation.liquidation_value_usd)).scalar() or 0
    
    # Stats by coin
    by_coin_query = query.with_entities(
        Liquidation.coin,
        func.count(Liquidation.id).label('count'),
        func.sum(Liquidation.liquidation_value_usd).label('value')
    ).group_by(Liquidation.coin)
    
    by_coin = {
        row.coin: {
            "count": row.count,
            "value_usd": float(row.value) if row.value else 0
        }
        for row in by_coin_query.all()
    }
    
    return LiquidationStatsResponse(
        total_liquidations=total_count,
        total_liquidation_value_usd=total_value,
        long_liquidations=long_count,
        long_liquidation_value_usd=long_value,
        short_liquidations=short_count,
        short_liquidation_value_usd=short_value,
        by_coin=by_coin
    )
