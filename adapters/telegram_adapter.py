from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from adapters import PlatformAdapter
from services.bot_service import BotResponse, UserAction

class TelegramAdapter(PlatformAdapter):
    """Telegram-specific adapter"""
    
    def convert_to_user_action(self, update: Update) -> UserAction:
        """Convert Telegram Update to UserAction"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Bạn"
        
        if update.message and update.message.text:
            if update.message.text.startswith('/start'):
                return UserAction(user_id, user_name, "start")
            else:
                return UserAction(user_id, user_name, "text_message", update.message.text)
        elif update.callback_query:
            return UserAction(user_id, user_name, "callback", update.callback_query.data)
        
        return UserAction(user_id, user_name, "unknown")
    
    async def send_response(self, response: BotResponse, update: Update):
        """Send response using Telegram API"""
        if response.action_type == "message":
            await update.message.reply_text(
                response.text, 
                reply_markup=response.keyboard_markup
            )
        elif response.action_type == "edit":
            await update.callback_query.edit_message_text(
                text=response.text,
                reply_markup=response.keyboard_markup
            )
            await update.callback_query.answer()
    
    def convert_keyboard(self, keyboard_markup) -> InlineKeyboardMarkup:
        """Telegram keyboards are already in correct format"""
        return keyboard_markup