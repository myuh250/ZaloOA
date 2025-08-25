import asyncio
import logging
from workers.follow_up_cron import run_follow_up_cron

logger = logging.getLogger(__name__)

async def cron_worker():
    """Run backup cron jobs daily - FALLBACK MECHANISM ONLY
    
    Chạy 1 lần/ngày để backup sync, vì chính chủ yếu dựa vào Apps Script webhook
    để realtime sync khi có form response mới.
    """
    logger.warning("Running backup cron worker - fallback mechanism")
    
    while True:
        try:
            await run_follow_up_cron()
            logger.info("Backup cron job completed")
        except Exception as e:
            logger.error(f"Error in backup cron job: {e}")
        
        # Sleep for 24 hours - backup sync only
        await asyncio.sleep(86400)  # 24 hours