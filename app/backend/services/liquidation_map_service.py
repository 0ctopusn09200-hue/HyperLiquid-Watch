import time
from decimal import Decimal
from typing import Optional, Dict, Any, List

import psycopg2
from config import settings


def _get_db_conn():
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def _auto_step(coin: str) -> Decimal:
    """
    价格分桶粒度：BTC 用 50/100 更好看；ETH 用 5/10；其余给个保守默认
    你也可以按你们前端想要的密度调整。
    """
    c = (coin or "").upper()
    if c == "BTC":
        return Decimal("50")
    if c == "ETH":
        return Decimal("5")
    if c in ("SOL",):
        return Decimal("1")
    return Decimal("1")


def get_liquidation_map(
    coin: str,
    window_seconds: int = 3600,
    step: Optional[Decimal] = None,
    limit_levels: int = 200,
) -> Dict[str, Any]:
    """
    从 liquidations 实时聚合：
    - 按 liquidation_price 分桶 (floor(price/step)*step)
    - 分 LONG/SHORT 统计 count & sum(value_usd)
    """
    coin_u = (coin or "").upper()
    if not coin_u:
        return {"coin": coin_u, "timestamp": time.time(), "price_levels": []}

    step = step or _auto_step(coin_u)

    sql = """
    WITH base AS (
      SELECT
        coin,
        side,
        liquidation_price::numeric AS price,
        COALESCE(liquidation_value_usd, 0)::numeric AS value_usd,
        block_timestamp
      FROM liquidations
      WHERE coin = %s
        AND block_timestamp >= (NOW() - (%s || ' seconds')::interval)
        AND liquidation_price IS NOT NULL
    ),
    bucketed AS (
      SELECT
        (FLOOR(price / %s) * %s)::numeric AS price_bucket,
        UPPER(COALESCE(side, '')) AS side_u,
        value_usd
      FROM base
    )
    SELECT
      price_bucket,
      SUM(CASE WHEN side_u IN ('BUY','LONG','L') THEN 1 ELSE 0 END)::int AS long_liquidation_count,
      SUM(CASE WHEN side_u IN ('SELL','SHORT','S') THEN 1 ELSE 0 END)::int AS short_liquidation_count,
      SUM(CASE WHEN side_u IN ('BUY','LONG','L') THEN value_usd ELSE 0 END)::numeric AS long_liquidation_value,
      SUM(CASE WHEN side_u IN ('SELL','SHORT','S') THEN value_usd ELSE 0 END)::numeric AS short_liquidation_value
    FROM bucketed
    GROUP BY price_bucket
    ORDER BY price_bucket DESC
    LIMIT %s;
    """

    conn = _get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, (coin_u, int(window_seconds), step, step, int(limit_levels)))
        rows = cur.fetchall()

        price_levels: List[Dict[str, Any]] = []
        for (price_bucket, lc, sc, lv, sv) in rows:
            # 这里字段名尽量贴近你 curl 输出的结构
            price_levels.append(
                {
                    "price": float(price_bucket),
                    "long_liquidation_count": int(lc or 0),
                    "short_liquidation_count": int(sc or 0),
                    "long_liquidation_value": float(lv or 0),
                    "short_liquidation_value": float(sv or 0),
                }
            )

        return {
            "coin": coin_u,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
            "price_levels": price_levels,
            "window_seconds": int(window_seconds),
            "step": float(step),
        }
    finally:
        cur.close()
        conn.close()
