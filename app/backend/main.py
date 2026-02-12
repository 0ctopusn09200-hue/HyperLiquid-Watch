"""
Main FastAPI application
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings

# Import routers
from routers import (
    liquidations,
    ratios,
    liquidation_map,
    transactions,
    whales,
    websocket,
    market,
    whale,
    wallet,
)

from kafka_consumer import kafka_consumer


# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


# ---------------- Lifespan ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle"""
    logger.info("[App] Starting Backend service...")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    # start kafka consumer
    kafka_consumer.set_main_loop(loop)
    kafka_consumer.start()

    logger.info(
        f"[App] Backend started on {settings.server_host}:{settings.server_port}"
    )
    yield

    logger.info("[App] Shutting down Backend service...")
    kafka_consumer.stop()
    logger.info("[App] Backend stopped")


# ---------------- Create FastAPI app ----------------
app = FastAPI(
    title="Hyperliquid Data Analysis API",
    description="Backend API for Hyperliquid perpetual order data analysis",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= ROUTERS =================

# -------- Frontend-compatible routes --------
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(whale.router, prefix=settings.api_prefix)
app.include_router(wallet.router, prefix=settings.api_prefix)

# -------- Core data routes --------
app.include_router(liquidations.router, prefix=settings.api_prefix)
app.include_router(ratios.router, prefix=settings.api_prefix)
app.include_router(liquidation_map.router, prefix=settings.api_prefix)  # ⭐关键
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(whales.router, prefix=settings.api_prefix)

# -------- WebSocket --------
app.include_router(websocket.router)


# ================= BASIC ENDPOINTS =================
@app.get("/")
async def root():
    return {
        "message": "Hyperliquid Data Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ---------------- Local run ----------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
        log_level="info",
    )
