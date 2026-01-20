"""
Wallet position distribution API routes (frontend-compatible)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal
from database import get_db
from schemas_frontend import (
    WalletPositionDistributionResponse,
    WalletPositionBucket,
    Sentiment
)
from models import Position
from sqlalchemy import func, case
from utils.formatters import format_currency

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/distribution")
async def get_wallet_distribution(
    token: Optional[str] = Query(None, description="Filter by token (default: all tokens aggregated)"),
    db: Session = Depends(get_db)
):
    """Get wallet position distribution"""
    try:
        # Query positions
        query = db.query(Position)
        
        if token:
            query = query.filter(Position.coin == token.upper())
        
        # Define position size buckets
        buckets_data = []
        
        # Bucket definitions: (min_value, max_value, category_key, category_en, position_size_label)
        bucket_definitions = [
            (0, 250, "shrimp", "Shrimp", "$0 - $250"),
            (250, 1000, "crab", "Crab", "$250 - $1K"),
            (1000, 10000, "fish", "Fish", "$1K - $10K"),
            (10000, 50000, "dolphin", "Dolphin", "$10K - $50K"),
            (50000, 100000, "shark", "Shark", "$50K - $100K"),
            (100000, 1000000, "whale", "Whale", "$100K - $1M"),
            (1000000, None, "mega_whale", "Mega Whale", "$1M+"),
        ]
        
        for min_val, max_val, category_key, category_en, position_size in bucket_definitions:
            # Calculate position value (size * mark_price)
            position_value_expr = Position.size * Position.mark_price
            
            # Filter by bucket range
            bucket_query = query.filter(position_value_expr >= min_val)
            if max_val is not None:
                bucket_query = bucket_query.filter(position_value_expr < max_val)
            
            # Aggregate stats
            bucket_stats = bucket_query.with_entities(
                func.count(func.distinct(Position.user_address)).label('wallet_count'),
                func.sum(case((Position.side == 'LONG', Position.size * Position.mark_price), else_=0)).label('long_value'),
                func.sum(case((Position.side == 'SHORT', Position.size * Position.mark_price), else_=0)).label('short_value'),
                func.sum(case((Position.side == 'LONG', 1), else_=0)).label('long_count'),
                func.sum(case((Position.side == 'SHORT', 1), else_=0)).label('short_count'),
                func.sum(case((Position.unrealized_pnl > 0, 1), else_=0)).label('profit_users'),
                func.sum(case((Position.unrealized_pnl < 0, 1), else_=0)).label('loss_users'),
            ).first()
            
            wallet_count = bucket_stats.wallet_count or 0
            long_value = bucket_stats.long_value or Decimal(0)
            short_value = bucket_stats.short_value or Decimal(0)
            total_value = long_value + short_value
            
            # Calculate percentages
            long_percent = float((long_value / total_value * 100)) if total_value > 0 else 0.0
            open_interest_percent = 0.0  # Will be calculated relative to total
            
            profit_users = bucket_stats.profit_users or 0
            loss_users = bucket_stats.loss_users or 0
            
            # Determine sentiment (simplified logic)
            if long_percent > 60:
                sentiment: Sentiment = "bullish"
            elif long_percent < 40:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            buckets_data.append({
                'wallet_count': wallet_count,
                'long_value': long_value,
                'short_value': short_value,
                'long_percent': long_percent,
                'open_interest_percent': open_interest_percent,
                'profit_users': profit_users,
                'loss_users': loss_users,
                'sentiment': sentiment,
                'position_size': position_size,
                'category': category_key,
                'category_en': category_en,
            })
        
        # Calculate total wallets and total open interest
        total_wallets = sum(b['wallet_count'] for b in buckets_data)
        total_open_interest = sum(float(b['long_value'] + b['short_value']) for b in buckets_data)
        
        # Calculate open interest percentages
        for bucket in buckets_data:
            bucket_value = float(bucket['long_value'] + bucket['short_value'])
            bucket['open_interest_percent'] = (bucket_value / total_open_interest * 100) if total_open_interest > 0 else 0.0
        
        # Convert to response format
        buckets = []
        for bucket in buckets_data:
            buckets.append(WalletPositionBucket(
                positionSize=bucket['position_size'],
                category=bucket['category'],
                categoryEn=bucket['category_en'],
                walletCount=bucket['wallet_count'],
                openInterestPercent=round(bucket['open_interest_percent'], 2),
                longValue=format_currency(bucket['long_value']),
                shortValue=format_currency(bucket['short_value']),
                longPercent=round(bucket['long_percent'], 2),
                profitUsers=bucket['profit_users'],
                lossUsers=bucket['loss_users'],
                sentiment=bucket['sentiment']
            ))
        
        # If no data, return mock data for development
        if total_wallets == 0:
            buckets = [
                WalletPositionBucket(
                    positionSize="$0 - $250",
                    category="shrimp",
                    categoryEn="Shrimp",
                    walletCount=0,
                    openInterestPercent=0.0,
                    longValue="$0",
                    shortValue="$0",
                    longPercent=50.0,
                    profitUsers=0,
                    lossUsers=0,
                    sentiment="neutral"
                )
            ]
        
        return WalletPositionDistributionResponse(
            buckets=buckets,
            totalWallets=total_wallets,
            updatedAt=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching wallet distribution: {str(e)}")
