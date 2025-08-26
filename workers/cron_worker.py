import asyncio
import urllib.request
import logging
from datetime import datetime, timezone, timedelta
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
    """Keep-alive worker - ping /health every 15 minutes with retry logic"""
    health_url = "https://zalooa.onrender.com/health"
    max_retries = 3
    retry_delay = 30  # seconds between retries
    
    while True:
        success = False
        for attempt in range(max_retries):
            try:
                # Increased timeout to 90 seconds with retry logic
                with urllib.request.urlopen(health_url, timeout=120) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive ping successful (attempt {attempt + 1})")
                        success = True
                        break
                    else:
                        logger.warning(f"⚠️ Keep-alive ping failed: HTTP {response.status} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"❌ Keep-alive error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        if not success:
            logger.critical(f"🚨 CRITICAL: Keep-alive failed after {max_retries} attempts. Service may sleep!")
        
        # Sleep for 15 minutes
        await asyncio.sleep(900)

def get_seconds_until_midnight_vn():
    """Calculate seconds until next 12:00 AM Vietnam time (UTC+7)"""
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz)
    
    # Get next midnight (12:00 AM)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate seconds until next midnight
    seconds_until = (next_midnight - now).total_seconds()
    
    return int(seconds_until), next_midnight

async def daily_worker():
    """Daily tasks - backup sync + token refresh at 12:00 AM Vietnam time"""
    logger.info("🔄 Daily worker started")
    
    while True:
        try:
            # Calculate time until next midnight VN
            seconds_until, next_midnight = get_seconds_until_midnight_vn()
            hours = seconds_until // 3600
            minutes = (seconds_until % 3600) // 60
            
            logger.info(f"⏰ Next cron job scheduled at {next_midnight.strftime('%Y-%m-%d %H:%M:%S')} VN time")
            logger.info(f"😴 Sleeping for {hours}h {minutes}m until midnight...")
            
            # Sleep until midnight Vietnam time
            await asyncio.sleep(seconds_until)
            
            logger.info("🌙 12:00 AM VN - Running daily cron jobs...")
            
            # 1. Follow-up messages (1 lần/ngày cho user chưa submit sau 24h)
            await run_follow_up_cron()
            logger.info("✅ Follow-up cron completed")
            
            # 2. Token refresh + Deploy (1 lần/ngày)
            await _refresh_tokens_with_deploy()
            logger.info("✅ Token refresh + deployment completed")
            
            logger.info("🎯 Daily cron jobs completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in daily jobs: {e}")
            # If error occurs, wait 1 hour before retrying
            logger.info("⚠️ Waiting 1 hour before retry...")
            await asyncio.sleep(3600)

async def _refresh_tokens_with_deploy():
    """Daily token refresh + deployment (1 lần/ngày lúc 12h đêm)"""
    try:
        token_service = get_token_management_service()
        
        # 1. Refresh tokens và update env vars
        result = await token_service.refresh_tokens_with_env_update()
        
        if not result["success"]:
            logger.error(f"Token refresh failed: {result['message']}")
            return
            
        logger.info("✅ Token refresh and env update successful")
        
        # 2. Trigger deployment để apply env vars mới (chỉ chạy 1 lần/ngày)
        deploy_result = await token_service.trigger_render_deploy()
        
        if deploy_result["success"]:
            logger.info("✅ Deployment triggered successfully")
        else:
            logger.warning(f"⚠️ Deploy trigger failed: {deploy_result['message']}")
            
    except Exception as e:
        logger.error(f"Token refresh + deploy error: {e}")