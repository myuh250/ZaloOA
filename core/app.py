from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.main import router as mainrouter
from core.logging import setup_logging

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Setup logging first
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title="Zalo OA Bot API",
        description="FastAPI application for Zalo Official Account Bot",
        version="1.0.0"
    )
    
    # Include routers
    app.include_router(mainrouter)
    
    # Serve static files
    app.mount("/static", StaticFiles(directory=".", html=True), name="static")
    
    return app