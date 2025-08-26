import asyncio
import urllib.request
import logging
from workers.follow_up_cron import run_follow_up_cron
from services.token_management_service import get_token_management_service

logger = logging.getLogger(__name__)

async def cron_worker():
    """Run cron jobs:
    1. Keep-alive ping every 15 minutes (prevent Render Free Tier sleep)
    2. Daily backup sync + token refresh
    """
    logger.info("Starting cron worker...")
    
    # Create tasks for concurrent execution
    keep_alive_task = asyncio.create_task(keep_alive_worker())
    daily_task = asyncio.create_task(daily_worker())
    
    # Run both tasks concurrently
    try:
        await asyncio.gather(keep_alive_task, daily_task)
    except Exception as e:
        logger.error(f"Error in cron worker: {e}")

async def keep_alive_worker():
    """Keep-alive worker - ping /health every 15 minutes"""
    health_url = "https://zalooa.onrender.com/health"
    
    while True:
        try:
            # Simple HTTP GET using urllib (no extra dependencies)
            with urllib.request.urlopen(health_url, timeout=30) as response:
                if response.status == 200:
                    logger.info("Keep-alive ping successful")
                else:
                    logger.warning(f"Keep-alive ping failed: {response.status}")
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
        
        # Sleep for 15 minutes
        await asyncio.sleep(900)

async def daily_worker():
    """Daily tasks - backup sync + token refresh"""
    logger.info("Starting daily worker")
    
    while True:
        try:
            # 1. Backup sync 
            await run_follow_up_cron()
            logger.info("Backup cron job completed")
            
            # 2. Auto refresh Zalo tokens
            await _refresh_tokens_cron()
            logger.info("Token refresh cron completed")
            
        except Exception as e:
            logger.error(f"Error in daily jobs: {e}")
        
        # Sleep for 24 hours
        await asyncio.sleep(86400)

async def _refresh_tokens_cron():
    """Helper function to refresh Zalo tokens"""
    try:
        token_service = get_token_management_service()
        result = await token_service.refresh_tokens_with_env_update()
        
        if result["success"]:
            logger.info("Automatic token refresh successful")
        else:
            logger.error(f"Automatic token refresh failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Token refresh cron error: {e}")