"""
Zalo Messaging Gateway - Infrastructure Layer
Concrete implementation cho Zalo platform
"""
import os
from core.interfaces.messaging_gateway import MessagingGateway
from services.bot_service import BotResponse
from core.messages import send_text_message


class ZaloMessagingGateway(MessagingGateway):
    """
    Concrete implementation for Zalo platform
    Infrastructure layer - biết specifics của Zalo API
    """

    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("ZALO_OA_ACCESS_TOKEN")

    async def send_response(self, response: BotResponse, user_id: str) -> None:
        """Send response using Zalo API"""
        if not response or not response.text or not user_id:
            return

        send_text_message(
            ZALO_OA_ACCESS_TOKEN=self.access_token,
            user_id=user_id,
            message_text=response.text
        )

    def parse_platform_data(self, raw_data: dict) -> dict:
        """Parse Zalo webhook data to standard format"""
        return {
            "user_id": str(raw_data.get("user_id", "")),
            "user_name": raw_data.get("user_name", "Bạn"),
            "message_text": raw_data.get("message", {}).get("text", ""),
            "event_type": raw_data.get("event_name", "unknown")
        }
