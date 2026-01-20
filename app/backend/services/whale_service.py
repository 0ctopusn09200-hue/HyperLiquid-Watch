"""
Service layer for whale watch operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from models import WhaleWatch, WhaleActivity
from schemas import WhaleWatchResponse, WhaleWatchCreate, WhaleActivityResponse


def get_whale_watches(
    db: Session,
    is_active: Optional[bool] = None
) -> List[WhaleWatchResponse]:
    """Get all whale watches"""
    query = db.query(WhaleWatch)
    
    if is_active is not None:
        query = query.filter(WhaleWatch.is_active == is_active)
    
    whales = query.all()
    return [WhaleWatchResponse.model_validate(w) for w in whales]


def create_whale_watch(
    db: Session,
    whale_data: WhaleWatchCreate
) -> WhaleWatchResponse:
    """Create a new whale watch"""
    whale = WhaleWatch(
        wallet_address=whale_data.wallet_address,
        alias=whale_data.alias,
        description=whale_data.description
    )
    
    db.add(whale)
    db.commit()
    db.refresh(whale)
    
    return WhaleWatchResponse.model_validate(whale)


def get_whale_activities(
    db: Session,
    whale_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    activity_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[WhaleActivityResponse], int]:
    """Get whale activities with pagination"""
    query = db.query(WhaleActivity)
    
    if whale_id:
        query = query.filter(WhaleActivity.whale_id == whale_id)
    if activity_type:
        query = query.filter(WhaleActivity.activity_type == activity_type)
    if start_time:
        query = query.filter(WhaleActivity.timestamp >= start_time)
    if end_time:
        query = query.filter(WhaleActivity.timestamp <= end_time)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    activities = query.order_by(desc(WhaleActivity.timestamp)).offset(offset).limit(page_size).all()
    
    return [WhaleActivityResponse.model_validate(a) for a in activities], total
