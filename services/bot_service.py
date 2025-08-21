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
        """Handle text messages"""
        if user_action.data and "tôi đã điền form" in user_action.data.lower():
            # Reuse existing callback logic instead of duplicating code
            callback_action = UserAction(
                user_id=user_action.user_id,
                user_name=user_action.user_name, 
                action_type="callback",
                data="form_filled"
            )
            return self.handle_callback(callback_action)
        return self.handle_user_stage(user_action)
    
    def handle_callback(self, user_action: UserAction) -> BotResponse:
        """Handle button callbacks"""
        if user_action.data == "welcome_start":
            self.form_service.increment_message_count(user_action.user_id)
            text, kb = self.form_service.get_form_message(user_action.user_name)
            return BotResponse(
                text=text,
                keyboard_markup=kb,
                action_type="edit"
            )
        elif user_action.data == "form_filled":
            self.form_service.mark_form_completed(user_action.user_id)
            return BotResponse(
                text=THANK_YOU,
                action_type="edit"
            )
        
        return BotResponse(text="Unknown action", action_type="message")
