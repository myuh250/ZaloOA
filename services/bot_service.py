from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from services.form_service import FormService, get_form_service
from services.llm_service import get_llm_service

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

    def handle_provide_field(self, user_action: UserAction) -> BotResponse:
        """Handle provide_field stage - collect email info"""
        
        # Get current user info
        current_info = self.form_service.get_user_info(user_action.user_id)
        
        # If this is the first time in provide_field stage (no message data yet)
        if not user_action.data or not user_action.data.strip():
            text, kb = self.form_service.get_provide_field_message(user_action.user_name)
            return BotResponse(
                text=text,
                keyboard_markup=kb,
                action_type="message"
            )
        
        # User has sent a message, try to extract email
        llm_service = get_llm_service()
        extracted = llm_service.extract_email(user_action.data)

        email_to_update = extracted.get('email') or current_info.get('email')
        if email_to_update:
            self.form_service.update_user_info(
                user_action.user_id,
                email=email_to_update
            )

        if self.form_service.has_provided_required_fields(user_action.user_id):
            return self.handle_second_interaction(user_action)
        
        updated_info = self.form_service.get_user_info(user_action.user_id)
        missing = []
        if not updated_info.get('email'):
            missing.append("email")
        
        if missing:
            missing_text = " và ".join(missing)
            response_text = f"Cảm ơn bạn! Tôi vẫn cần thêm thông tin về: {missing_text}. Vui lòng cung cấp đầy đủ thông tin để tiếp tục."
        else:
            response_text = "Cảm ơn bạn! Thông tin đã được cập nhật."
        
        return BotResponse(
            text=response_text,
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
        elif stage == 'provide_field':
            return self.handle_provide_field(user_action)
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
            return self.handle_callback(callback_action)
        
        # For first time users - always respond (no slash command needed)
        if self.form_service.is_first_time_user(user_action.user_id):
            return self.handle_user_stage(user_action)
        
        # Check if user has completed form (submitted status)
        if self.form_service.has_completed_form(user_action.user_id):
            # For completed users - ONLY respond if slash command present
            if self.has_slash_command(user_action.data):
                return self.handle_user_stage(user_action)
            # No response - let human conversation continue
            return BotResponse(
                text="",  # Empty response = no reply
                action_type="ignore"
            )
        
        # For users still in form completion process (pending status)
        user_stage = self.form_service.get_user_stage(user_action.user_id)
        if user_stage == 'provide_field':
            # Still need to collect email - always respond
            return self.handle_user_stage(user_action)
        
        # For other existing users - only respond if slash command present
        if self.has_slash_command(user_action.data):
            return self.handle_user_stage(user_action)
        
        # No response - let human conversation continue
        return BotResponse(
            text="",  # Empty response = no reply
            action_type="ignore"
        )
        
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
            # Kiểm tra xem user đã thực sự điền form hay chưa
            if self.form_service.has_completed_form(user_action.user_id):
                # Đã điền thật -> xác nhận hoàn thành
                self.form_service.mark_form_completed(user_action.user_id)
                return BotResponse(
                    text=THANK_YOU,
                    action_type="edit"
                )
            else:
                # Chưa điền thật -> gửi lại message follow up
                current_stage_response = self.handle_user_stage(user_action)
                return BotResponse(
                    text=current_stage_response.text,
                    keyboard_markup=current_stage_response.keyboard_markup,
                    action_type="edit"
                )
        
        return BotResponse(text="Unknown action", action_type="message")
        
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
