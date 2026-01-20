"""
Market API routes (frontend-compatible)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db
from services import liquidation_map_service, ratio_service
from schemas_frontend import (
    LiquidationHeatmapResponse,
    LiquidationPoint,
    LongShortRatioResponse
)
from models import LiquidationMap, LongShortRatio
from sqlalchemy import func, desc

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/liquidation")
async def get_liquidation_heatmap(
    token: str = Query("BTC", description="Token symbol (default: BTC)"),
    range_percent: Optional[float] = Query(4.5, alias="range", description="Price range percentage (default: 4.5%)"),
    db: Session = Depends(get_db)
):
    """Get liquidation heatmap for a token"""
    try:
        # Get latest liquidation map data
        latest_map = liquidation_map_service.get_liquidation_map(db, token.upper(), None, None, None)
        
        if not latest_map.price_levels:
            # Return empty response if no data
            return LiquidationHeatmapResponse(
                token=token.upper(),
                currentPrice=0.0,
                points=[],
                minPrice=0.0,
                maxPrice=0.0
            )
        
        # Extract prices and find current price (middle point or highest liquidation price)
        prices = [float(level.price) for level in latest_map.price_levels]
        current_price = sum(prices) / len(prices) if prices else 0.0
        
        # Calculate price range
        range_amount = current_price * (range_percent / 100)
        min_price = current_price - range_amount
        max_price = current_price + range_amount
        
        # Filter and format points
        points = []
        for level in latest_map.price_levels:
            price = float(level.price)
            if min_price <= price <= max_price:
                # Convert liquidation value to volume units (divide by 10000 for display multiplier)
                long_vol = float(level.long_liquidation_value) / 10000 if level.long_liquidation_value else 0.0
                short_vol = float(level.short_liquidation_value) / 10000 if level.short_liquidation_value else 0.0
                
                points.append(LiquidationPoint(
                    price=price,
                    longVol=long_vol,
                    shortVol=short_vol,
                    current=(abs(price - current_price) < (current_price * 0.001))  # Within 0.1% of current price
                ))
        
        # Sort by price
        points.sort(key=lambda x: x.price)
        
        # Ensure current price point exists
        if not any(p.current for p in points):
            # Add current price point if missing
            current_point = LiquidationPoint(
                price=current_price,
                longVol=0.0,
                shortVol=0.0,
                current=True
            )
            points.append(current_point)
            points.sort(key=lambda x: x.price)
        
        # Update min/max from actual points
        if points:
            min_price = min(p.price for p in points)
            max_price = max(p.price for p in points)
        
        return LiquidationHeatmapResponse(
            token=token.upper(),
            currentPrice=current_price,
            points=points,
            minPrice=min_price,
            maxPrice=max_price
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching liquidation heatmap: {str(e)}")


@router.get("/long-short-ratio")
async def get_long_short_ratio(
    token: Optional[str] = Query(None, description="Filter by token (default: all tokens aggregated)"),
    db: Session = Depends(get_db)
):
    """Get global long/short ratio"""
    try:
        # Get current ratios
        if token:
            ratios = ratio_service.get_current_ratios(db, token.upper())
        else:
            ratios = ratio_service.get_current_ratios(db, None)
        
        # Aggregate if multiple coins
        total_long_value = Decimal(0)
        total_short_value = Decimal(0)
        total_long_24h_ago = Decimal(0)
        total_short_24h_ago = Decimal(0)
        
        for ratio in ratios:
            total_long_value += ratio.long_position_value
            total_short_value += ratio.short_position_value
        
        # Calculate 24h change (simplified - would need historical data for accurate calculation)
        # For now, return 0 or placeholder
        # TODO: Implement actual 24h comparison when historical data is available
        
        # Get ratios from 24h ago for comparison
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        if token:
            historical_query = db.query(LongShortRatio).filter(
                LongShortRatio.coin == token.upper(),
                LongShortRatio.timestamp <= twenty_four_hours_ago
            ).order_by(desc(LongShortRatio.timestamp)).first()
        else:
            # Aggregate all coins 24h ago
            historical_ratios = db.query(LongShortRatio).filter(
                LongShortRatio.timestamp <= twenty_four_hours_ago
            ).all()
            for hr in historical_ratios:
                total_long_24h_ago += hr.long_position_value
                total_short_24h_ago += hr.short_position_value
        
        # Calculate percentages (0-100)
        total_value = total_long_value + total_short_value
        if total_value > 0:
            long_percent = float((total_long_value / total_value) * 100)
            short_percent = float((total_short_value / total_value) * 100)
        else:
            long_percent = 50.0
            short_percent = 50.0
        
        # Calculate 24h changes
        total_24h_ago = total_long_24h_ago + total_short_24h_ago
        if total_long_24h_ago > 0:
            long_change_24h = float(((total_long_value - total_long_24h_ago) / total_long_24h_ago) * 100)
        else:
            long_change_24h = 0.0
        
        if total_short_24h_ago > 0:
            short_change_24h = float(((total_short_value - total_short_24h_ago) / total_short_24h_ago) * 100)
        else:
            short_change_24h = 0.0
        
        return LongShortRatioResponse(
            longPercent=round(long_percent, 2),
            shortPercent=round(short_percent, 2),
            longVolume=float(total_long_value),
            shortVolume=float(total_short_value),
            longChange24h=round(long_change_24h, 2),
            shortChange24h=round(short_change_24h, 2),
            updatedAt=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching long/short ratio: {str(e)}")
