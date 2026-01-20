"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from config import settings
import asyncio


# Import routers
from routers import liquidations, ratios, liquidation_map, transactions, whales, websocket
from kafka_consumer import kafka_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    print("Starting Backend service...")
    
    # Set main event loop for Kafka consumer
    loop = asyncio.get_event_loop()
    kafka_consumer.set_main_loop(loop)
    kafka_consumer.start()
    
    print(f"Backend service started on {settings.server_host}:{settings.server_port}")
    
    yield
    
    # Shutdown
    print("Shutting down Backend service...")
    kafka_consumer.stop()
    print("Backend service stopped")


# Create FastAPI app
app = FastAPI(
    title="Hyperliquid Data Analysis API",
    description="Backend API for Hyperliquid perpetual order data analysis",
    version="1.0.0",
    lifespan=lifespan
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
from routers import market, whale, wallet

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
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
