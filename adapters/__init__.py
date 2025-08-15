from abc import ABC, abstractmethod
from services.bot_service import BotResponse, UserAction

class PlatformAdapter(ABC):
    """Abstract base class for platform adapters"""
    
    @abstractmethod
    def convert_to_user_action(self, platform_data) -> UserAction:
        """Convert platform-specific data to UserAction"""
        pass
    
    @abstractmethod
    async def send_response(self, response: BotResponse, platform_context):
        """Send BotResponse using platform-specific methods"""
        pass
    
    @abstractmethod
    def convert_keyboard(self, keyboard_markup) -> any:
        """Convert generic keyboard to platform-specific format"""
        pass