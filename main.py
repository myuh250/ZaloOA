import asyncio
import uvicorn
from core.app import create_app
from core.config import settings

# Create the FastAPI application
app = create_app()

async def main():
    """Main entry point"""
    config = uvicorn.Config(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())