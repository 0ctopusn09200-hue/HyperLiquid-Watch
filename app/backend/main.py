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
from routers import liquidations, ratios, liquidation_map, transactions, whales, websocket
from routers import market, whale, wallet

from kafka_consumer import kafka_consumer

# Logging setup (make logs visible in docker logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("[App] Starting Backend service...")

    # Get the running event loop for scheduling async tasks from consumer thread
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    kafka_consumer.set_main_loop(loop)
    kafka_consumer.start()

    logger.info(f"[App] Backend service started on {settings.server_host}:{settings.server_port}")

    yield

    logger.info("[App] Shutting down Backend service...")
    kafka_consumer.stop()
    logger.info("[App] Backend service stopped")


# Create FastAPI app
app = FastAPI(
    title="Hyperliquid Data Analysis API",
    description="Backend API for Hyperliquid perpetual order data analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Frontend-compatible routes
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(whale.router, prefix=settings.api_prefix)
app.include_router(wallet.router, prefix=settings.api_prefix)

# Legacy routes (for backward compatibility, can be removed later)
app.include_router(liquidations.router, prefix=settings.api_prefix)
app.include_router(ratios.router, prefix=settings.api_prefix)
app.include_router(liquidation_map.router, prefix=settings.api_prefix)
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(whales.router, prefix=settings.api_prefix)

# WebSocket router (no prefix needed, already includes /api/v1/ws)
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hyperliquid Data Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # Local run (no reload; keep it stable)
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
        log_level="info",
    )
