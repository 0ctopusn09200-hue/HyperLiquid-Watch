"""
Service layer for long/short ratio operations (Plan A)
REALTIME from `liquidations` table (no dependency on long_short_ratios table).

We define:
- long liquidation  := side == 'SELL'
- short liquidation := side == 'BUY'
Then ratio can be computed from liquidation_value_usd over a time window.

If your frontend expects other meaning, swap SELL/BUY mapping below.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from schemas import LongShortRatioResponse


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_decimal(v) -> Decimal:
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def get_current_ratios(db: Session, coin: Optional[str] = None) -> List[LongShortRatioResponse]:
    """
    Return current ratios computed from last 5 minutes liquidation flow.
    """
    return _get_ratios_window(db, coin=coin, window_seconds=300)


def get_ratio_history(
    db: Session,
    coin: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[LongShortRatioResponse], int]:
    """
    Simple "history" computed by windowing in DB is expensive.
    For now we return snapshots by minute buckets using `liquidations`.
    """
    coin = (coin or "").upper().strip()
    if not coin:
        return [], 0

    if end_time is None:
        end_time = _utcnow()
    if start_time is None:
        start_time = end_time - timedelta(hours=1)

    # bucket per minute
    rows = db.execute(
        text(
            """
            WITH x AS (
              SELECT
                date_trunc('minute', block_timestamp) AS ts,
                side,
                COALESCE(liquidation_value_usd, 0)::numeric AS v
              FROM liquidations
              WHERE coin = :coin
                AND block_timestamp >= :start
                AND block_timestamp <= :end
            )
            SELECT
              ts,
              SUM(CASE WHEN UPPER(side)='SELL' THEN v ELSE 0 END)::numeric AS long_v,
              SUM(CASE WHEN UPPER(side)='BUY'  THEN v ELSE 0 END)::numeric AS short_v
            FROM x
            GROUP BY ts
            ORDER BY ts DESC
            """
        ),
        {"coin": coin, "start": start_time, "end": end_time},
    ).fetchall()

    total = len(rows)
    offset = (page - 1) * page_size
    page_rows = rows[offset : offset + page_size]

    out: List[LongShortRatioResponse] = []
    for ts, long_v, short_v in page_rows:
        long_v = _to_decimal(long_v)
        short_v = _to_decimal(short_v)
        total_v = long_v + short_v
        long_pct = float(long_v / total_v) if total_v > 0 else 0.0
        short_pct = float(short_v / total_v) if total_v > 0 else 0.0
        ratio = float(long_v / short_v) if short_v > 0 else (float("inf") if long_v > 0 else 0.0)

        out.append(
            LongShortRatioResponse(
                coin=coin,
                timestamp=ts,
                long_ratio=long_pct,
                short_ratio=short_pct,
                long_short_ratio=ratio,
            )
        )

    return out, total


def _get_ratios_window(db: Session, coin: Optional[str], window_seconds: int) -> List[LongShortRatioResponse]:
    now = _utcnow()
    start = now - timedelta(seconds=window_seconds)

    if coin:
        coins = [(coin.upper().strip(),)]
    else:
        coins = db.execute(text("SELECT DISTINCT coin FROM liquidations")).fetchall()

    results: List[LongShortRatioResponse] = []

    for (c,) in coins:
        if not c:
            continue

        row = db.execute(
            text(
                """
                SELECT
                  SUM(CASE WHEN UPPER(side)='SELL' THEN COALESCE(liquidation_value_usd,0) ELSE 0 END)::numeric AS long_v,
                  SUM(CASE WHEN UPPER(side)='BUY'  THEN COALESCE(liquidation_value_usd,0) ELSE 0 END)::numeric AS short_v
                FROM liquidations
                WHERE coin = :coin
                  AND block_timestamp >= :start
                  AND block_timestamp <= :end
                """
            ),
            {"coin": c, "start": start, "end": now},
        ).fetchone()

        long_v = _to_decimal(row[0] if row else 0)
        short_v = _to_decimal(row[1] if row else 0)
        total_v = long_v + short_v

        long_pct = float(long_v / total_v) if total_v > 0 else 0.0
        short_pct = float(short_v / total_v) if total_v > 0 else 0.0
        ratio = float(long_v / short_v) if short_v > 0 else (float("inf") if long_v > 0 else 0.0)

        results.append(
            LongShortRatioResponse(
                coin=c,
                timestamp=now,
                long_ratio=long_pct,
                short_ratio=short_pct,
                long_short_ratio=ratio,
            )
        )

    return results
