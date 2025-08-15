from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from services.bot_service import BotService
from adapters.telegram_adapter import TelegramAdapter

# Initialize services
bot_service = BotService()
telegram_adapter = TelegramAdapter()

async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal handler using adapter pattern"""
    
    # Please change adapter based on your platform
    user_action = telegram_adapter.convert_to_user_action(update)
    
    # Route to appropriate handler based on action type
    if user_action.action_type == "start":
        response = bot_service.handle_start_command(user_action)
    elif user_action.action_type == "callback":
        response = bot_service.handle_callback(user_action)
    elif user_action.action_type == "text_message":
        response = bot_service.handle_text_message(user_action)
    else:
        return
    
    # Send response using adapter
    await telegram_adapter.send_response(response, update)

def register_handlers(application):
    """Register handlers with the application"""
    # Single handler for telegram only
    # For other platforms, create their own adapters and handlers
    application.add_handler(CommandHandler("start", handle_update))
    application.add_handler(CallbackQueryHandler(handle_update))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update))