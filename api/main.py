from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from core.usecases.message_usecase import MessageUseCase, ProcessMessageRequest
from core.deps import MessageUseCaseDep
from workers.follow_up_cron import run_sync_form_responses
from services.token_management_service import get_token_management_service
from core.config import settings
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "message": "Zalo OA Bot API is running"
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

@router.post("/status-changed")
async def status_change_webhook(request: Request):
    """
    Apps Script webhook - nhận thông báo khi status thay đổi từ pending → submitted
    Gửi tin nhắn cảm ơn trực tiếp qua Zalo OA
    """
    try:
        # Parse data từ Apps Script
        data = await request.json()
        user_id = data.get("id")  # ID của user từ sheet
        username = data.get("username", "Bạn")
        email = data.get("email", "")
        old_status = data.get("old_status", "")
        new_status = data.get("new_status", "")
        
        logger.info(f"Status change webhook - User: {username} (ID: {user_id}), Email: {email}, Status: {old_status} → {new_status}")
        
        # Chỉ xử lý khi status chuyển từ pending/other → submitted
        if new_status == "submitted" and old_status != "submitted":
            # Import services cần thiết
            from services.bot_service import BotService, UserAction
            from services.form_service import get_form_service
            from adapters.zalo_messaging_gateway import ZaloMessagingGateway
            
            # Khởi tạo services
            form_service = get_form_service()
            bot_service = BotService(form_service)
            zalo_gateway = ZaloMessagingGateway()
            
            # Tạo response message
            response = bot_service.handle_completed(UserAction(
                user_id=str(user_id),
                user_name=username,
                action_type="completed"
            ))
            
            # Gửi tin nhắn cảm ơn qua Zalo
            await zalo_gateway.send_response(response, str(user_id))
            
            logger.info(f"Thank you message sent to {username} (ID: {user_id}): {response.text}")
            
            return {
                "status": "success",
                "message": f"Thank you message sent to {username}",
                "user_id": user_id
            }
        else:
            return {
                "status": "ignored", 
                "message": f"Status change ignored: {old_status} → {new_status}"
            }
            
    except Exception as e:
        logger.error(f"Status change webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/refresh-zalo-token")
async def refresh_zalo_token():
    """
    Manually refresh Zalo access token và update vào Render environment
    API endpoint để test token refresh process
    """
    try:
        token_service = get_token_management_service()
        result = await token_service.refresh_tokens_with_env_update()
        
        if not result["success"]:
            if result.get("step") == "update_environment":
                # Partial success: token refreshed but env update failed
                return {
                    "status": "partial_success",
                    "message": "Token refreshed but failed to update Render environment",
                    "token_data": result.get("token_data"),
                    "env_error": result["message"]
                }
            else:
                return {"status": "error", "message": result["message"]}
        
        logger.info("Successfully refreshed token and updated Render environment")
        return {
            "status": "success",
            "message": result["message"],
            "token_expires_in": result.get("token_expires_in"),
            "updated_at": result.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/token-status")
async def check_token_status():
    """
    Check current Zalo token status - for monitoring/debugging
    """
    return {
        "status": "info",
        "has_access_token": bool(settings.zalo_oa_access_token),
        "has_refresh_token": bool(settings.zalo_oa_refresh_token),
        "has_app_id": bool(settings.zalo_app_id),
        "has_secret_key": bool(settings.zalo_secret_key),
        "has_render_config": bool(settings.render_service_id and settings.render_api_key)
    }

# Function to be called by cron worker
async def refresh_zalo_tokens_cron():
    """
    Function được gọi bởi cron worker để tự động refresh tokens
    """
    try:
        token_service = get_token_management_service()
        result = await token_service.refresh_tokens_with_env_update()
        return result["success"]
        
    except Exception as e:
        logger.error(f"Cron token refresh error: {e}")
        return False