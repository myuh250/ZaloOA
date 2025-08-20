from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from core.usecases.message_usecase import MessageUseCase, ProcessMessageRequest
from core.deps import MessageUseCaseDep
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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
    Zalo Webhook Controller - chỉ handle HTTP layer
    Clean Architecture: Controller chỉ parse request và delegate to UseCase
    """
    # 1. Parse HTTP request
    logger.info(f"Headers: {dict(request.headers)}")
    data = await request.json()
    logger.info(f"Webhook payload: {data}")
    
    # 1.1. Filter chỉ xử lý event từ user gửi tin nhắn
    event_name = data.get("event_name", "")
    if event_name != "user_send_text":
        logger.info(f"Ignored event: {event_name}")
        return {"status": "ignored", "message": f"Event {event_name} ignored"}
    
    # 2. Extract data từ request (HTTP concern)
    user_id = str(data.get("sender", {}).get("id", ""))
    user_name = data.get("user_name", "Bạn") 
    message_text = data.get("message", {}).get("text", "")
    
    # 3. Create request DTO
    process_request = ProcessMessageRequest(
        user_id=user_id,
        user_name=user_name,
        message_text=message_text,
        platform_data=data
    )
    
    # 4. Delegate to UseCase (business logic)
    result = await message_usecase.process_message(process_request)
    
    # 5. Return HTTP response
    if result.success:
        logger.info(f"Message processed successfully: {result.response_text}")
        return {"status": "received", "message": result.message}
    else:
        logger.error(f"Processing failed: {result.message}")
        return {"status": "error", "message": result.message}