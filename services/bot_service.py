from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from services.form_service import FormService, get_form_service

# Constants
THANK_YOU = "Cảm ơn bạn đã hoàn thành form! 🙏"

@dataclass
class BotResponse:
    """Standardized response format for any platform"""
    text: str
    buttons: Optional[list] = None
    keyboard_markup: Optional[Any] = None  # Platform-specific keyboard
    action_type: str = "message"  # message, edit, callback_answer
    
@dataclass
class UserAction:
    """Standardized user action format"""
    user_id: int
    user_name: str
    action_type: str  # start, callback, text_message
    data: Optional[str] = None  # callback data or message text

class BotService:
    """Core bot logic - platform independent"""
    
    def __init__(self, form_service: FormService = None):
        self.form_service = form_service or get_form_service()
    
    def handle_first_time(self, user_action: UserAction) -> BotResponse:
        self.form_service.mark_user_as_seen(user_action.user_id, user_action.user_name)
        text, kb = self.form_service.get_welcome_message(user_action.user_name)
        return BotResponse(
            text=text,
            keyboard_markup=kb,
            action_type="message"
        )

    def handle_second_interaction(self, user_action: UserAction) -> BotResponse:
        self.form_service.increment_message_count(user_action.user_id)
        text, kb = self.form_service.get_form_message(user_action.user_name)
        return BotResponse(
            text=text,
            keyboard_markup=kb,
            action_type="message"
        )

    def handle_follow_up(self, user_action: UserAction) -> BotResponse:
        self.form_service.increment_message_count(user_action.user_id)
        text, kb = self.form_service.get_after_interaction_message(user_action.user_name)
        return BotResponse(
            text=text,
            keyboard_markup=kb,
            action_type="message"
        )

    def handle_completed(self, user_action: UserAction) -> BotResponse:
        return BotResponse(
            text=THANK_YOU,
            action_type="message"
        )

    def handle_user_stage(self, user_action: UserAction) -> BotResponse:
        """Handle user interaction based on their stage"""
        stage = self.form_service.get_user_stage(user_action.user_id)

        if stage == 'first_time':
            return self.handle_first_time(user_action)
        elif stage == 'second_interaction':
            return self.handle_second_interaction(user_action)
        elif stage == 'follow_up':
            return self.handle_follow_up(user_action)
        else:  # completed
            return self.handle_completed(user_action)

    def handle_start_command(self, user_action: UserAction) -> BotResponse:
        """Handle /start command or initial user interaction"""
        return self.handle_user_stage(user_action)
    
    def handle_text_message(self, user_action: UserAction) -> BotResponse:
        """Handle text messages with slash command requirement"""
        
        # Always handle form completion (this is response to bot)
        if self.is_form_completion_message(user_action.data):
            callback_action = UserAction(
                user_id=user_action.user_id,
                user_name=user_action.user_name, 
                action_type="callback",
                data="form_filled"
            )
            return self.handle_user_stage(callback_action)
        
        # For first time users - always respond (no slash command needed)
        if self.form_service.is_first_time_user(user_action.user_id):
            return self.handle_user_stage(user_action)
        
        # For existing users - only respond if slash command present
        if self.has_slash_command(user_action.data):
            return self.handle_user_stage(user_action)
        
        # No response - let human conversation continue
        return BotResponse(
            text="",  # Empty response = no reply
            action_type="ignore"
        )
        
    def has_slash_command(self, text: str) -> bool:
        """Check if message contains slash command"""
        if not text:
            return False
        
        text = text.strip().lower()
        
        # List of supported slash commands
        commands = ['/support']
        
        return any(text.startswith(cmd) for cmd in commands)

    def is_form_completion_message(self, text: str) -> bool:
        """Check if message indicates form completion"""
        if not text:
            return False
        return "tôi đã điền form" in text.lower()
