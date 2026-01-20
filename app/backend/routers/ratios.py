"""
Long/Short ratio API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from services import ratio_service
from schemas import ApiResponse, PaginatedResponse, PaginationInfo

router = APIRouter(prefix="/long-short-ratios", tags=["long-short-ratios"])


@router.get("/current")
async def get_current_ratios(
    coin: Optional[str] = Query(None, description="Filter by coin"),
    db: Session = Depends(get_db)
):
    """Get current long/short ratios"""
    ratios = ratio_service.get_current_ratios(db, coin)
    
    return ApiResponse(data={"ratios": [r.model_dump() for r in ratios]})


@router.get("/history")
async def get_ratio_history(
    coin: str = Query(..., description="Coin symbol"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get long/short ratio history"""
    ratios, total = ratio_service.get_ratio_history(
        db, coin, start_time, end_time, page, page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data={
            "items": [r.model_dump() for r in ratios],
            "pagination": PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            ).model_dump()
        }
    )
