from fastapi import APIRouter, Request
from bot.messages import send_text_message
import os

router = APIRouter()
ZALO_OA_ACCESS_TOKEN = os.getenv("ZALO_OA_ACCESS_TOKEN")

@router.post("/webhook")
async def zalo_webhook(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if user_id:
        send_text_message(ZALO_OA_ACCESS_TOKEN, user_id, message_text="Xin chào từ FastAPI!")
    return {"status": "received"}