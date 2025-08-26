import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from workers.cron_worker import cron_worker
from api.main import router as mainrouter
from core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - handle startup and shutdown"""
    
    # Startup: Start cron worker as background task
    cron_task = asyncio.create_task(cron_worker())
    
    yield  # App is running
    
    # Shutdown: Cancel cron worker
    cron_task.cancel()
    try:
        await cron_task
    except asyncio.CancelledError:
        pass


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