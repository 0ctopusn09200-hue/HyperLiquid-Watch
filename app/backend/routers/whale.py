"""
Whale API routes (frontend-compatible)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal
from database import get_db
from services import whale_service, transaction_service
from schemas_frontend import (
    WhaleActivitiesResponse,
    WhaleTransaction,
    PositionSide,
    PositionType
)
from models import WhaleActivity, Transaction
from utils.formatters import format_relative_time, truncate_address, format_token_amount
from sqlalchemy import or_, and_

router = APIRouter(prefix="/whale", tags=["whale"])


@router.get("/activities")
async def get_whale_activities(
    limit: int = Query(10, ge=1, le=100, description="Number of transactions (default: 10)"),
    token: Optional[str] = Query(None, description="Filter by token"),
    side: Optional[PositionSide] = Query(None, description="Filter by position side"),
    type: Optional[PositionType] = Query(None, description="Filter by transaction type"),
    minValue: float = Query(1000000, description="Minimum USD value (default: 1000000)"),
    db: Session = Depends(get_db)
):
    """Get whale activities"""
    try:
        # Query whale activities and large transactions
        query = db.query(WhaleActivity)
        
        # Apply filters
        if token:
            query = query.filter(WhaleActivity.coin == token.upper())
        
        if side:
            # Map "Long"/"Short" to database format
            side_filter = "LONG" if side == "Long" else "SHORT"
            query = query.filter(WhaleActivity.activity_type.like(f"%{side_filter}%"))
        
        if type:
            # Map "Open"/"Close" to activity type
            type_filter = "OPEN" if type == "Open" else "CLOSE"
            query = query.filter(WhaleActivity.activity_type.like(f"%{type_filter}%"))
        
        # Filter by minimum value
        query = query.filter(WhaleActivity.value_usd >= Decimal(str(minValue)))
        
        # Get total count
        total_count = query.count()
        
        # Order by timestamp descending and limit
        activities = query.order_by(WhaleActivity.timestamp.desc()).limit(limit).all()
        
        # Convert to frontend format
        transactions = []
        for activity in activities:
            # Parse side and type from activity_type
            activity_type_upper = activity.activity_type.upper()
            pos_side: PositionSide = "Long" if "LONG" in activity_type_upper else "Short"
            pos_type: PositionType = "Open" if "OPEN" in activity_type_upper else "Close"
            
            # Format amount
            amount_str = ""
            if activity.size and activity.coin:
                amount_str = format_token_amount(activity.size, activity.coin)
            elif activity.coin:
                amount_str = f"0 {activity.coin}"
            
            # Format time
            time_str = format_relative_time(activity.timestamp)
            
            # Format address
            address_str = truncate_address(activity.wallet_address)
            
            transactions.append(WhaleTransaction(
                time=time_str,
                address=address_str,
                token=activity.coin or "N/A",
                value=float(activity.value_usd) if activity.value_usd else 0.0,
                side=pos_side,
                type=pos_type,
                amount=amount_str,
                timestamp=activity.timestamp.isoformat() + "Z",
                txHash=activity.tx_hash
            ))
        
        # Also query large transactions from transactions table
        tx_query = db.query(Transaction).filter(
            Transaction.fee.isnot(None),  # Has fee means significant transaction
        )
        
        if token:
            tx_query = tx_query.filter(Transaction.coin == token.upper())
        
        if side:
            side_filter = "LONG" if side == "Long" else "SHORT"
            tx_query = tx_query.filter(Transaction.side == side_filter)
        
        # Filter by size * price (approximate value)
        # This is a simplified filter, actual implementation may need more logic
        large_txs = tx_query.filter(
            (Transaction.size * Transaction.price) >= Decimal(str(minValue))
        ).order_by(Transaction.block_timestamp.desc()).limit(limit).all()
        
        # Add large transactions to the list
        for tx in large_txs:
            # Determine if it's an open or close (simplified logic)
            pos_type: PositionType = "Open" if tx.tx_type in ["ORDER", "OPEN"] else "Close"
            pos_side: PositionSide = "Long" if tx.side in ["LONG", "L"] else "Short"
            
            # Calculate value
            value = float(tx.size * tx.price) if tx.size and tx.price else 0.0
            
            if value >= minValue:
                amount_str = format_token_amount(tx.size, tx.coin)
                time_str = format_relative_time(tx.block_timestamp)
                address_str = truncate_address(tx.user_address)
                
                transactions.append(WhaleTransaction(
                    time=time_str,
                    address=address_str,
                    token=tx.coin,
                    value=value,
                    side=pos_side,
                    type=pos_type,
                    amount=amount_str,
                    timestamp=tx.block_timestamp.isoformat() + "Z",
                    txHash=tx.tx_hash
                ))
        
        # Sort by timestamp (most recent first) and remove duplicates
        seen_hashes = set()
        unique_transactions = []
        for tx in sorted(transactions, key=lambda x: x.timestamp or "", reverse=True):
            if tx.txHash and tx.txHash not in seen_hashes:
                seen_hashes.add(tx.txHash)
                unique_transactions.append(tx)
            elif not tx.txHash:
                unique_transactions.append(tx)
        
        # Limit to requested number
        unique_transactions = unique_transactions[:limit]
        total_count = max(total_count, len(unique_transactions))
        
        return WhaleActivitiesResponse(
            transactions=unique_transactions,
            totalCount=total_count,
            updatedAt=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching whale activities: {str(e)}")
