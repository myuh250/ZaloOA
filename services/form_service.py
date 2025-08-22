from datetime import datetime, timezone
from typing import Optional, Dict, Tuple, Any
from core.config import settings
from services.google_sheets_service import GoogleSheetsService, get_sheets_service

DEFAULT_USER_NAME = "User" # Default username if can not get username form platform

class FormService:
    """Service to handle form-related operations"""
    
    def __init__(self, sheets_service: GoogleSheetsService = None, template_service=None):
        self.sheets_service = sheets_service or get_sheets_service()
        self.default_user_name = DEFAULT_USER_NAME
        # Lazy import to avoid circular dependency
        if template_service is None:
            from services.template_service import get_template_service
            self.template_service = get_template_service()
        else:
            self.template_service = template_service
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data from sheets"""
        return self.sheets_service.get_user(user_id)

    def is_first_time_user(self, user_id: str) -> bool:
        """Check if user is completely new (never seen before)"""
        return self.get_user(user_id) is None

    def mark_user_as_seen(self, user_id: str, username: str = None) -> bool:
        """Mark user as seen for the first time"""
        username = username or self.default_user_name
        return self.sheets_service.add_user(user_id, username, 'pending')

    def mark_form_completed(self, user_id: str) -> bool:
        """Mark that user completed the form"""
        return self.sheets_service.mark_form_submitted(user_id)

    def has_completed_form(self, user_id: str) -> bool:
        """Check if user completed the form"""
        user = self.get_user(user_id)
        return user and user.get('form_status') == 'submitted'
    
    def has_provided_required_fields(self, user_id: str) -> bool:
        """Check if user has provided required fields (email)"""
        return self.sheets_service.has_complete_user_info(user_id)

    def get_user_message_count(self, user_id: str) -> int:
        """
        Get how many messages user has sent based on time tracking.
        0: chưa từng tương tác
        1: đã tương tác 1 lần (chưa có last_follow_up_sent)
        2: đã có last_follow_up_sent (tức là 2+ lần)
        """
        user = self.get_user(user_id)
        if not user:
            return 0
        if not user.get('last_follow_up_sent'):
            return 1
        # Có last_follow_up_sent, tức là 2+ lần
        return 2

    def get_user_stage(self, user_id: str) -> str:
        """
        Determine what stage user is in:
        - 'first_time': Never seen before -> template_welcome_1
        - 'provide_field': Just seen, need to collect name/email -> template_customercare_1
        - 'second_interaction': Has name/email, 1st interaction -> template_customercare_2  
        - 'follow_up': Has 2+ interactions, pending status -> template_customercare_3
        - 'completed': Has completed form -> thank you message
        """
        if self.is_first_time_user(user_id):
            return 'first_time'
        if self.has_completed_form(user_id):
            return 'completed'
        user = self.get_user(user_id)
        if not user or user.get('form_status') != 'pending':
            return 'completed'
        
        # Check if user has provided required fields (name and email)
        if not self.has_provided_required_fields(user_id):
            return 'provide_field'
        
        message_count = self.get_user_message_count(user_id)
        if message_count == 1:
            return 'second_interaction'
        return 'follow_up'

    def mark_follow_up_sent(self, user_id: str) -> bool:
        """Mark that follow-up message was sent"""
        return self.sheets_service.mark_follow_up_sent(user_id)
        
    def increment_message_count(self, user_id: str) -> None:
        """
        Update last_follow_up_sent for second interaction.
        For subsequent interactions, rely on time comparison in get_user_stage.
        """
        user = self.get_user(user_id)
        if user and not user.get('last_follow_up_sent'):
            self.mark_follow_up_sent(user_id)

    def get_welcome_message(self, user_name: str = None) -> Tuple[str, Any]:
        """Get welcome message using template"""
        user_name = user_name or self.default_user_name
        return self.template_service.get_welcome_message(user_name)

    def get_form_message(self, user_name: str = None) -> Tuple[str, Any]:
        """Get customer care form message using template"""
        user_name = user_name or self.default_user_name
        return self.template_service.get_customercare_message(user_name, settings.form_url)

    def get_after_interaction_message(self, user_name: str = None) -> Tuple[str, Any]:
        """Get reminder message after user interaction using template"""
        user_name = user_name or self.default_user_name
        return self.template_service.get_reminder_message(user_name, settings.form_url)
    
    def get_provide_field_message(self, user_name: str = None) -> Tuple[str, Any]:
        """Get message to collect user information using template_customercare_1"""
        user_name = user_name or self.default_user_name
        return self.template_service.get_customercare_1_message(user_name)
    
    def update_user_info(self, user_id: str, email: str = None) -> bool:
        """Update user's email information"""
        return self.sheets_service.update_user_info(user_id, email)
    
    def get_user_info(self, user_id: str) -> dict:
        """Get user's current email information"""
        user = self.get_user(user_id)
        if not user:
            return {'email': ''}
        
        return {
            'email': user.get('email', '').strip()
        }

# Global instance for backward compatibility
_form_service = None

def get_form_service() -> FormService:
    """Get FormService singleton instance"""
    global _form_service
    if _form_service is None:
        _form_service = FormService()
    return _form_service

# Backward compatibility: Keep only essential functions for external access
def get_user(user_id):
    """DEPRECATED: Use FormService.get_user() instead"""
    return get_form_service().get_user(user_id)