"""
Service layer for long/short ratio operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Optional, List
from datetime import datetime
from models import LongShortRatio
from schemas import LongShortRatioResponse


def get_current_ratios(
    db: Session,
    coin: Optional[str] = None
) -> List[LongShortRatioResponse]:
    """Get current long/short ratios"""
    if coin:
        # Get latest ratio for specific coin
        ratio = db.query(LongShortRatio).filter(
            LongShortRatio.coin == coin
        ).order_by(desc(LongShortRatio.timestamp)).first()
        
        if ratio:
            return [LongShortRatioResponse.model_validate(ratio)]
        return []
    else:
        # Get latest ratio for each coin
        # Using DISTINCT ON (PostgreSQL specific)
        subquery = db.query(
            LongShortRatio.coin,
            func.max(LongShortRatio.timestamp).label('max_timestamp')
        ).group_by(LongShortRatio.coin).subquery()
        
        ratios = db.query(LongShortRatio).join(
            subquery,
            and_(
                LongShortRatio.coin == subquery.c.coin,
                LongShortRatio.timestamp == subquery.c.max_timestamp
            )
        ).all()
        
        return [LongShortRatioResponse.model_validate(r) for r in ratios]


def get_ratio_history(
    db: Session,
    coin: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[LongShortRatioResponse], int]:
    """Get ratio history with pagination"""
    query = db.query(LongShortRatio).filter(LongShortRatio.coin == coin)
    
    if start_time:
        query = query.filter(LongShortRatio.timestamp >= start_time)
    if end_time:
        query = query.filter(LongShortRatio.timestamp <= end_time)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    ratios = query.order_by(desc(LongShortRatio.timestamp)).offset(offset).limit(page_size).all()
    
    return [LongShortRatioResponse.model_validate(r) for r in ratios], total
