from fastapi import APIRouter, Request
from bot.messages import send_text_message
import os
import logging

router = APIRouter()
ZALO_OA_ACCESS_TOKEN = os.getenv("ZALO_OA_ACCESS_TOKEN")

logger = logging.getLogger(__name__)

@router.post("/webhook")
async def zalo_webhook(request: Request):
    logger.info(f"Headers: {dict(request.headers)}")
    data = await request.json()
    logger.info(f"Webhook payload: {data}")
    body = await request.body()
    logger.info(f"Raw body: {body.decode('utf-8')}")
    
    user_id = data.get("user_id")
    if user_id:
        logger.info(f"Sending reply to user_id={user_id}")
        send_text_message(ZALO_OA_ACCESS_TOKEN, user_id, message_text="Xin chào từ FastAPI!")
    
    return {"status": "received"}