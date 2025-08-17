from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.webhook import router
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from bot.handlers import register_handlers
from cronjobs.follow_up_cron import run_follow_up_cron
import asyncio
import uvicorn
import os
import logging
import sys

# --- Logging setup ---
import watchtower
import boto3

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Push logs to CloudWatch
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-southeast-1"),  
)

log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "MyFastAPIAppLogs")

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group=log_group,
    stream_name=os.getenv("RENDER_SERVICE_ID", "fastapi-service"),
    create_log_group=True,
)

logging.getLogger().addHandler(cloudwatch_handler)
logger = logging.getLogger(__name__)

# --- App setup ---
app = FastAPI()

async def cron_worker():
    """Run cron jobs periodically"""
    while True:
        try:
            await run_follow_up_cron()
            logger.info("Cron job completed")
        except Exception as e:
            logger.error(f"Error in cron job: {e}")
        await asyncio.sleep(60)

# Zalo verification routes
@app.get("/zalo_verifierUERWBlpADnKQr-8ntgHQC2EaYHVFqbvBDp4q.html")
async def zalo_verification():
    """Serve Zalo verification file"""
    verification_file = "zalo_verifierUERWBlpADnKQr-8ntgHQC2EaYHVFqbvBDp4q.html"
    if os.path.exists(verification_file):
        return FileResponse(verification_file, media_type="text/html")
    return {"error": "Verification file not found"}

# Include API routes
app.include_router(router)

# Serve static files
app.mount("/static", StaticFiles(directory=".", html=True), name="static")

async def main():
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())