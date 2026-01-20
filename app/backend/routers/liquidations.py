"""
Liquidation API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from services import liquidation_service
from schemas import ApiResponse, PaginatedResponse, PaginationInfo

router = APIRouter(prefix="/liquidations", tags=["liquidations"])


@router.get("/recent")
async def get_recent_liquidations(
    coin: Optional[str] = Query(None, description="Filter by coin"),
    side: Optional[str] = Query(None, description="Filter by side (LONG/SHORT)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Get recent liquidation events"""
    liquidations = liquidation_service.get_recent_liquidations(db, coin, side, limit)
    
    return ApiResponse(
        data={"liquidations": [liq.model_dump() for liq in liquidations]}
    )


@router.get("")
async def get_liquidations(
    coin: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get liquidations with pagination"""
    liquidations, total = liquidation_service.get_liquidations(
        db, coin, side, start_time, end_time, page, page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data={
            "items": [liq.model_dump() for liq in liquidations],
            "pagination": PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            ).model_dump()
        }
    )


@router.get("/stats")
async def get_liquidation_stats(
    coin: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get liquidation statistics"""
    stats = liquidation_service.get_liquidation_stats(db, coin, start_time, end_time)
    
    return ApiResponse(data=stats.model_dump())
