import asyncio
import logging
from workers.follow_up_cron import run_follow_up_cron
from services.token_management_service import get_token_management_service

logger = logging.getLogger(__name__)

async def cron_worker():
    """Run daily cron jobs - FALLBACK MECHANISM + TOKEN REFRESH
    
    1. Backup sync form responses (fallback mechanism)
    2. Auto refresh Zalo access token (primary function)
    Chạy 1 lần/ngày
    """
    logger.warning("Running daily cron worker - backup sync + token refresh")
    
    while True:
        try:
            # 1. Backup sync 
            await run_follow_up_cron()
            logger.info("Backup cron job completed")
            
            # 2. Auto refresh Zalo tokens
            await _refresh_tokens_cron()
            logger.info("Token refresh cron completed")
            
        except Exception as e:
            logger.error(f"Error in cron jobs: {e}")
        
        # Sleep for 24 hours
        await asyncio.sleep(86400)  # 24 hours

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