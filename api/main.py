from fastapi import APIRouter, Request
from core.messages import send_text_message
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
ZALO_OA_ACCESS_TOKEN = os.getenv("ZALO_OA_ACCESS_TOKEN")

@router.get("/zalo_verifierUERWBlpADnKQr-8ntgHQC2EaYHVFqbvBDp4q.html")
async def zalo_verification():
    """Serve Zalo verification file"""
    verification_file = "zalo_verifierUERWBlpADnKQr-8ntgHQC2EaYHVFqbvBDp4q.html"
    if os.path.exists(verification_file):
        return FileResponse(verification_file, media_type="text/html")
    return {"error": "Verification file not found"}

@router.get("/callback")
async def zalo_oauth_callback(request: Request):
    """Handle Zalo OAuth callback"""
    params = dict(request.query_params)
    logger.info(f"Zalo OAuth callback received. Query params: {params}")
    oa_id = params.get("oa_id")
    code = params.get("code")

    return {"status": "ok", "oa_id": oa_id, "code": code, "message": "OAuth callback received"}

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