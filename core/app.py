import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.main import router as mainrouter
from core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - handle startup and shutdown"""
    
    # NOTE: Cron workers removed to prevent event loop blocking on weak servers (512MB + 0.1 CPU)
    # - Keep-alive ping was blocking webhook processing with sync urllib calls
    # - External traffic (webhooks) naturally prevents Render from sleeping
    # - Daily tasks can be handled by external schedulers if needed (Apps Script, GitHub Actions, etc.)
    
    yield  # App is running
    
    # No background tasks to cleanup


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup logging first
    setup_logging()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Zalo OA Bot API",
        description="FastAPI application for Zalo Official Account Bot",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Include routers
    app.include_router(mainrouter)
    
    # Serve static files
    app.mount("/static", StaticFiles(directory=".", html=True), name="static")
    
    return app