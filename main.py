from fastapi import FastAPI
from api.webhook import router
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from bot.handlers import register_handlers
from cronjobs.follow_up_cron import run_follow_up_cron
import asyncio
import threading
import time
import uvicorn

async def cron_worker():
    """Run cron jobs periodically"""
    while True:
        try:
            await run_follow_up_cron()
            print("Cron job completed\n")
        except Exception as e:
            print(f"Error in cron job: {e}")

        await asyncio.sleep(60)

def start_cron_thread():
    """Start cron in separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cron_worker())
    
def start_fastapi():
    """Start FastAPI server in a separate thread"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

app = FastAPI()
app.include_router(router)

def main():
    # Start FastAPI server in a separate thread
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()

    # Start cron job in a separate thread
    cron_thread = threading.Thread(target=start_cron_thread, daemon=True)
    cron_thread.start()

    # Start Telegram bot (blocking)
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(telegram_app)
    telegram_app.run_polling()

if __name__ == "__main__":
    main()