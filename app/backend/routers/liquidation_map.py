"""
Liquidation map API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal
from database import get_db
from services import liquidation_map_service
from schemas import ApiResponse

router = APIRouter(prefix="/liquidation-map", tags=["liquidation-map"])


@router.get("")
async def get_liquidation_map(
    coin: str = Query(..., description="Coin symbol"),
    timestamp: Optional[datetime] = Query(None, description="Specific timestamp, latest if not provided"),
    price_range: Optional[str] = Query(None, description="Price range in format 'min,max'"),
    db: Session = Depends(get_db)
):
    """Get liquidation map for a coin"""
    price_min = None
    price_max = None
    
    if price_range:
        try:
            parts = price_range.split(",")
            if len(parts) == 2:
                price_min = Decimal(parts[0].strip()) if parts[0].strip() else None
                price_max = Decimal(parts[1].strip()) if parts[1].strip() else None
        except Exception:
            pass
    
    map_data = liquidation_map_service.get_liquidation_map(
        db, coin, timestamp, price_min, price_max
    )
    
    return ApiResponse(data=map_data.model_dump())
