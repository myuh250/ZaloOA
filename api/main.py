from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from core.usecases.message_usecase import MessageUseCase, ProcessMessageRequest, MessageRequestDTO
from core.deps import (
    MessageUseCaseDep,
    get_background_manager,
    FormSyncUseCaseDep,
    StatusChangeUseCaseDep,
)
from core.usecases.status_change_usecase import StatusChangedDTO
from core.usecases.form_sync_usecase import FormSubmittedDTO
from core.config import settings
import os
import logging
import asyncio
from utils.rate_limit import is_rate_limited
from workers.tasks import process_message_background

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_ping():
    """
    Simple health endpoint for keep-alive pings
    Optimized for external monitoring services and cron jobs
    """
    return {
        "status": "healthy",
        "timestamp": "ok",
        "uptime": "running"
    }

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
async def zalo_webhook(
    request: Request,
    message_usecase: MessageUseCaseDep
):
    """
    Fast Response Zalo Webhook - Return 200 OK immediately to prevent retries
    Process message in background to avoid timeout issues
    """
    try:
        # 1. Parse HTTP request
        data = await request.json()
        logger.info(f"Webhook payload: {data}")
        
        # 2. Filter chỉ xử lý event từ user gửi tin nhắn
        event_name = data.get("event_name", "")
        if event_name != "user_send_text":
            logger.info(f"Ignored event: {event_name}")
            return {"status": "ignored", "message": f"Event {event_name} ignored"}
        
        # 3. Extract user data and check rate limiting
        user_id = str(data.get("sender", {}).get("id", ""))
        if is_rate_limited(user_id):
            logger.info(f"Rate limited message from user {user_id}")
            return {"status": "rate_limited", "message": "Please wait before sending another message"}
        
        # 4. Extract remaining data
        user_name = data.get("user_name", "Bạn") 
        message_text = data.get("message", {}).get("text", "")
        
        # 5. Create request DTO (framework-agnostic)
        dto = MessageRequestDTO.from_webhook(data)

        # 6. START BACKGROUND PROCESSING via background manager
        background = get_background_manager()
        background.run(process_message_background, message_usecase, ProcessMessageRequest(
            user_id=dto.user_id,
            user_name=dto.user_name,
            message_text=dto.message_text,
            platform_data=dto.raw_data,
        ))
        
        # 7. Fast response to prevent retries (< 100ms response time)
        return {"status": "received", "message": "Processing message"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": "Failed to process webhook"}

@router.post("/form-submitted")
async def form_submitted_webhook(
    request: Request,
    form_sync: FormSyncUseCaseDep,
):
    """
    Google Apps Script webhook - đơn giản xử lý khi có form response mới
    Chỉ cần có email thì chạy sync
    """
    try:
        data = await request.json()
        dto = FormSubmittedDTO(**data)
        result = await form_sync.run_sync(dto)
        return result
            
    except Exception as e:
        logger.error(f"Form webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/status-changed")
async def status_change_webhook(
    request: Request,
    status_usecase: StatusChangeUseCaseDep,
):
    """
    Apps Script webhook - nhận thông báo khi status thay đổi từ pending → submitted
    Gửi tin nhắn cảm ơn trực tiếp qua Zalo OA
    """
    try:
        data = await request.json()
        
        dto = StatusChangedDTO(**data)
        logger.info(
            f"Status change webhook - User: {dto.username} (ID: {dto.id}), Email: {dto.email}, Status: {dto.old_status} → {dto.new_status}"
        )
        result = await status_usecase.handle(dto)
        return result
            
    except Exception as e:
        logger.error(f"Status change webhook error: {e}")
        return {"status": "error", "message": str(e)}
