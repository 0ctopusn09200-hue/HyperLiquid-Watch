"""
Transaction API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from services import transaction_service
from schemas import ApiResponse, PaginatedResponse, PaginationInfo

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("")
async def get_transactions(
    user_address: Optional[str] = Query(None),
    coin: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    tx_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get transactions with pagination"""
    transactions, total = transaction_service.get_transactions(
        db, user_address, coin, side, tx_type, start_time, end_time, page, page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        data={
            "items": [tx.model_dump() for tx in transactions],
            "pagination": PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages
            ).model_dump()
        }
    )


@router.get("/{tx_hash}")
async def get_transaction(
    tx_hash: str,
    db: Session = Depends(get_db)
):
    """Get transaction by hash"""
    transaction = transaction_service.get_transaction_by_hash(db, tx_hash)
    
    if not transaction:
        return ApiResponse(code=404, message="Transaction not found", data=None)
    
    return ApiResponse(data=transaction.model_dump())
