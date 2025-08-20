import os
from adapters import PlatformAdapter
from services.bot_service import BotResponse, UserAction
# NOTE: Legacy adapter - không được sử dụng trong Clean Architecture hiện tại
# ZaloMessagingGateway được sử dụng thay thế
# from core.messages import send_text_message  # REMOVED: Di chuyển vào ZaloMessagingGateway

class ZaloAdapter(PlatformAdapter):
    """ZaloOA-specific adapter"""
    
    def __init__(self):
        self.access_token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    
    def convert_to_user_action(self, zalo_data) -> UserAction:
        """Convert ZaloOA webhook data to UserAction"""
        user_id = str(zalo_data.get("user_id", ""))
        user_name = zalo_data.get("user_name", "Bạn")
        
        # Determine action type based on Zalo webhook data structure
        if zalo_data.get("event_name") == "user_send_text":
            message_text = zalo_data.get("message", {}).get("text", "")
            return UserAction(
                user_id=user_id,
                user_name=user_name, 
                action_type="text_message",
                data=message_text
            )
        elif zalo_data.get("event_name") == "follow":
            return UserAction(
                user_id=user_id,
                user_name=user_name,
                action_type="start"
            )
        else:
            return UserAction(
                user_id=user_id,
                user_name=user_name,
                action_type="unknown"
            )


        