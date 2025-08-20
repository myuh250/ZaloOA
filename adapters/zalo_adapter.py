import os
from adapters import PlatformAdapter
from services.bot_service import BotResponse, UserAction
from core.messages import send_text_message

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
    
    async def send_response(self, response: BotResponse, zalo_context):
        """Send response using ZaloOA API"""
        if not response or not response.text:
            return
            
        user_id = zalo_context.get("user_id")
        if user_id and self.access_token:
            send_text_message(
                ZALO_OA_ACCESS_TOKEN=self.access_token,
                user_id=str(user_id),
                message_text=response.text
            )

        