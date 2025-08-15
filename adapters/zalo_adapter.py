from adapters import PlatformAdapter
from services.bot_service import BotResponse, UserAction
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class ZaloAdapter(PlatformAdapter):
    """ZaloOA-specific adapter - to be implemented by ZaloOA team"""
    
    def convert_to_user_action(self, zalo_data) -> UserAction:
        """Convert ZaloOA webhook data to UserAction"""
        # TODO: ZaloOA team implements this
    
    async def send_response(self, response: BotResponse, zalo_context):
        """Send response using ZaloOA API"""
        # TODO: ZaloOA team implements this
    
    def convert_keyboard(self, telegram_keyboard: InlineKeyboardMarkup):
        """Convert Telegram keyboard to ZaloOA format"""
        # TODO: ZaloOA team implements this
        