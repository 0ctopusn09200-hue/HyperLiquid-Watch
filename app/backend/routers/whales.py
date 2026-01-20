"""
Whale watch API routes
"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from services import whale_service
from schemas import ApiResponse, PaginatedResponse, PaginationInfo, WhaleWatchCreate

router = APIRouter(prefix="/whales", tags=["whales"])


@router.get("")
async def get_whale_watches(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all whale watches"""
    whales = whale_service.get_whale_watches(db, is_active)
    
    return ApiResponse(data={"whales": [w.model_dump() for w in whales]})


@router.post("")
async def create_whale_watch(
    whale_data: WhaleWatchCreate,
    db: Session = Depends(get_db)
):
    """Create a new whale watch"""
    whale = whale_service.create_whale_watch(db, whale_data)
    
    return ApiResponse(data=whale.model_dump())


@router.get("/{whale_id}/activities")
async def get_whale_activities(
    whale_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    activity_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get whale activities"""
    activities, total = whale_service.get_whale_activities(
        db, whale_id, start_time, end_time, activity_type, page, page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data={
            "items": [a.model_dump() for a in activities],
            "pagination": PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            ).model_dump()
        }
    )
