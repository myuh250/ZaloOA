"""
Zalo Messaging Gateway - Infrastructure Layer
Concrete implementation cho Zalo platform
"""
import os
import requests
import json
from core.interfaces.messaging_gateway import MessagingGateway
from services.bot_service import BotResponse


class ZaloMessagingGateway(MessagingGateway):
    """
    Concrete implementation for Zalo platform
    Infrastructure layer - biết specifics của Zalo API
    """

    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("ZALO_OA_ACCESS_TOKEN")
        self.api_url = "https://openapi.zalo.me/v3.0/"

    def _send_text_message(self, user_id: str, message_text: str = None, message_file: str = None) -> dict:
        """Private method - Send text message via Zalo API"""
        url = self.api_url + "oa/message/cs"
        headers = {
            "Content-Type": "application/json",
            "access_token": self.access_token
        }
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {}
        }

        if message_text and message_file:
            raise ValueError("Both message_text and message_file cannot be provided at the same time")
        elif message_text:
            data["message"]["text"] = message_text
        elif message_file:
            with open(message_file, "r") as f:
                data["message"]["text"] = f.read()
        else:
            raise ValueError("Either message_text or message_file must be provided")

        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        try:
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}
        except Exception as e:
            return {"error": str(e)}

    async def send_response(self, response: BotResponse, user_id: str) -> None:
        """Send response using Zalo API"""
        if not response or not response.text or not user_id:
            return

        result = self._send_text_message(
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
