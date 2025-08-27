from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.bot_service import BotService, UserAction
from core.interfaces.messaging_gateway import MessagingGateway


class StatusChangedDTO(BaseModel):
    id: str
    username: Optional[str] = "Bạn"
    email: Optional[str] = ""
    old_status: Optional[str] = ""
    new_status: Optional[str] = ""


class StatusChangeUseCase:
    def __init__(self, bot_service: BotService, gateway: MessagingGateway):
        self.bot_service = bot_service
        self.gateway = gateway

    async def handle(self, dto: StatusChangedDTO) -> Dict[str, Any]:
        """Handle status change business flow and send message if needed."""
        if dto.new_status == "submitted" and dto.old_status != "submitted":
            response = self.bot_service.handle_completed(UserAction(
                user_id=str(dto.id),
                user_name=dto.username or "Bạn",
                action_type="completed"
            ))

            await self.gateway.send_response(response, str(dto.id))

            return {
                "status": "success",
                "message": f"Thank you message sent to {dto.username}",
                "user_id": dto.id
            }

        return {
            "status": "ignored",
            "message": f"Status change ignored: {dto.old_status} → {dto.new_status}"
        }


