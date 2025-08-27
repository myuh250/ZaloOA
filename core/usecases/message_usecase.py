"""
Message Processing Use Case - Application Layer
Xử lý business logic độc lập với platform
"""
import asyncio
from dataclasses import dataclass
from pydantic import BaseModel
from services.bot_service import BotService, UserAction, BotResponse
from core.interfaces.messaging_gateway import MessagingGateway


@dataclass
class ProcessMessageRequest:
    """Request DTO for message processing"""
    user_id: str
    user_name: str
    message_text: str
    platform_data: dict


class MessageRequestDTO(BaseModel):
    user_id: str
    user_name: str
    message_text: str
    raw_data: dict

    @classmethod
    def from_webhook(cls, data: dict):
        return cls(
            user_id=str(data.get("sender", {}).get("id", "")),
            user_name=data.get("user_name", "Bạn"),
            message_text=data.get("message", {}).get("text", ""),
            raw_data=data,
        )


@dataclass
class ProcessMessageResponse:
    """Response DTO for message processing"""
    success: bool
    message: str
    response_text: str = ""


class MessageUseCase:
    """
    Use Case for processing incoming messages
    Contains pure business logic, không biết về platform specifics
    """
    
    def __init__(self, bot_service: BotService, message_gateway: MessagingGateway):
        self.bot_service = bot_service
        self.message_gateway = message_gateway
    
    async def process_message(self, request: ProcessMessageRequest) -> ProcessMessageResponse:
        """
        Process incoming message - pure business logic
        """
        try:
            # Convert to domain model
            user_action = UserAction(
                user_id=request.user_id,
                user_name=request.user_name,
                action_type="text_message",
                data=request.message_text
            )
            
            # Business logic - route to appropriate handler based on action type
            if user_action.action_type == "text_message":
                response = self.bot_service.handle_text_message(user_action)
            elif user_action.action_type == "start":
                response = self.bot_service.handle_start_command(user_action)
            elif user_action.action_type == "callback":
                response = self.bot_service.handle_callback(user_action)
            else:
                response = self.bot_service.handle_start_command(user_action)
            
            # Add delay to give LLM time to process before potential follow-up messages
            # Only delay if we have a response to send (not empty/ignore responses)
            if response.action_type != "ignore" and response.text.strip():
                await asyncio.sleep(2.5)  # Wait 2.5 seconds
            
            # Send through gateway (abstraction layer)
            await self.message_gateway.send_response(response, request.user_id)
            
            return ProcessMessageResponse(
                success=True,
                message="Message processed successfully",
                response_text=response.text
            )
            
        except Exception as e:
            return ProcessMessageResponse(
                success=False,
                message=f"Error processing message: {str(e)}"
            )
