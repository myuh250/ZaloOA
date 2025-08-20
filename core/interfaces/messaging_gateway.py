"""
Messaging Gateway Interface - Domain Layer
Pure abstraction, không có implementation details
"""
from abc import ABC, abstractmethod
from services.bot_service import BotResponse


class MessagingGateway(ABC):
    """
    Abstract Gateway for messaging platforms
    Thuộc Domain layer - pure abstraction
    UseCase layer sẽ depend vào interface này (Dependency Inversion)
    """
    
    @abstractmethod
    async def send_response(self, response: BotResponse, user_id: str) -> None:
        """Send response through platform-specific implementation"""
        pass
    
    @abstractmethod
    def parse_platform_data(self, raw_data: dict) -> dict:
        """Parse platform-specific data to standard format"""
        pass
