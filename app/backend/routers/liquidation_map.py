from fastapi import APIRouter, Query
from decimal import Decimal
from typing import Optional

from services.liquidation_map_service import get_liquidation_map

router = APIRouter()


@router.get("/liquidation-map")
def liquidation_map(
    coin: str = Query(..., description="e.g. BTC"),
    window_seconds: int = Query(3600, ge=60, le=86400),
    step: Optional[float] = Query(None, description="price bucket step, e.g. 50 for BTC"),
    limit_levels: int = Query(200, ge=10, le=2000),
):
    data = get_liquidation_map(
        coin=coin,
        window_seconds=window_seconds,
        step=Decimal(str(step)) if step is not None else None,
        limit_levels=limit_levels,
    )
    return {"code": 200, "message": "success", "data": data}
