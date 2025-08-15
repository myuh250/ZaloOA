from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from services.form_service import (
    mark_user_as_seen, increment_message_count,
    mark_form_completed, get_user_stage,
    get_welcome_message, get_form_message, get_after_interaction_message
)
from bot.messages import THANK_YOU

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
    
    def handle_first_time(self, user_action: UserAction) -> BotResponse:
        mark_user_as_seen(user_action.user_id, user_action.user_name)
        text, kb = get_welcome_message(user_action.user_name)
        return BotResponse(
            text=text,
            keyboard_markup=kb,
            action_type="message"
        )

    def handle_second_interaction(self, user_action: UserAction) -> BotResponse:
        increment_message_count(user_action.user_id)
        text, kb = get_form_message(user_action.user_name)
        return BotResponse(
            text=text,
            keyboard_markup=kb,
            action_type="message"
        )

    def handle_follow_up(self, user_action: UserAction) -> BotResponse:
        increment_message_count(user_action.user_id)
        text, kb = get_after_interaction_message(user_action.user_name)
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
        stage = get_user_stage(user_action.user_id)

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
        return self.handle_user_stage(user_action)
    
    def handle_callback(self, user_action: UserAction) -> BotResponse:
        """Handle button callbacks"""
        if user_action.data == "welcome_start":
            increment_message_count(user_action.user_id)
            text, kb = get_form_message(user_action.user_name)
            return BotResponse(
                text=text,
                keyboard_markup=kb,
                action_type="edit"
            )
        elif user_action.data == "form_filled":
            mark_form_completed(user_action.user_id)
            return BotResponse(
                text=THANK_YOU,
                action_type="edit"
            )
        
        return BotResponse(text="Unknown action", action_type="message")
