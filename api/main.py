from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from core.usecases.message_usecase import MessageUseCase, ProcessMessageRequest
from core.deps import MessageUseCaseDep
from workers.follow_up_cron import run_sync_form_responses
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
    # logger.info(f"Headers: {dict(request.headers)}")
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
        # logger.info(f"Message processed successfully: {result.response_text}")
        return {"status": "received", "message": result.message}
    else:
        # logger.error(f"Processing failed: {result.message}")
        return {"status": "error", "message": result.message}

@router.post("/form-submitted")
async def form_submitted_webhook(request: Request):
    """
    Google Apps Script webhook - đơn giản xử lý khi có form response mới
    Chỉ cần có email thì chạy sync
    """
    try:
        # Parse request data từ Apps Script
        data = await request.json()
        email = data.get("email", "").strip().lower()
        
        # Chỉ cần có email thì chạy sync
        if email:
            logger.info(f"Form webhook received - Email: {email}")
            
            updated_users = await run_sync_form_responses()
            
            logger.info(f"Webhook sync completed - Updated {len(updated_users)} users")
            
            return {
                "status": "success", 
                "processed": len(updated_users)
            }
        else:
            return {"status": "ignored", "message": "No email provided"}
            
    except Exception as e:
        logger.error(f"Form webhook error: {e}")
        return {"status": "error", "message": str(e)}