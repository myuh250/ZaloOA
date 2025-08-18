import asyncio
import logging
from workers.follow_up_cron import run_follow_up_cron

logger = logging.getLogger(__name__)

async def cron_worker():
    """Run cron jobs periodically - FOR DEVELOPMENT ONLY
    
    In production, use proper task queue like Celery + Redis
    """
    logger.warning("Running cron worker in development mode")
    
    while True:
        try:
            await run_follow_up_cron()
            logger.info("Cron job completed")
        except Exception as e:
            logger.error(f"Error in cron job: {e}")
        
        # Sleep for 1 hour instead of 60 seconds
        await asyncio.sleep(3600)  # 1 hour

# Uncomment below to run cron worker (not recommended for production)
# async def start_background_tasks():
#     """Start background tasks"""
#     asyncio.create_task(cron_worker())