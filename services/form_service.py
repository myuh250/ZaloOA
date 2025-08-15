from datetime import datetime, timezone
from config import FORM_URL
from services.template_service import (
    get_welcome_template_message,
    get_customercare_template_message, 
    get_reminder_template_message
)
from services.google_sheets_service import get_sheets_service

DEFAULT_USER_NAME = "User" # Default username if can not get username form platform

def get_user(user_id):
    sheets = get_sheets_service()
    return sheets.get_user(user_id)

def is_first_time_user(user_id):
    """Check if user is completely new (never seen before)"""
    return get_user(user_id) is None

def mark_user_as_seen(user_id, username=DEFAULT_USER_NAME):
    """Mark user as seen for the first time"""
    sheets = get_sheets_service()
    return sheets.add_user(user_id, username, 'pending')

def mark_form_completed(user_id):
    """Mark that user completed the form"""
    sheets = get_sheets_service()
    return sheets.mark_form_submitted(user_id)

def has_completed_form(user_id):
    """Check if user completed the form"""
    user = get_user(user_id)
    return user and user.get('form_status') == 'submitted'

def get_user_message_count(user_id):
    """
    Get how many messages user has sent based on time tracking.
    0: chưa từng tương tác
    1: đã tương tác 1 lần (chưa có last_follow_up_sent)
    2: đã có last_follow_up_sent (tức là 2+ lần)
    """
    user = get_user(user_id)
    if not user:
        return 0
    if not user.get('last_follow_up_sent'):
        return 1
    # Có last_follow_up_sent, tức là 2+ lần
    return 2

def get_user_stage(user_id):
    """
    Determine what stage user is in:
    - 'first_time': Never seen before -> template_welcome_1
    - 'second_interaction': Has 1 interaction, pending status -> template_customercare_2  
    - 'follow_up': Has 2+ interactions, pending status -> template_customercare_3
    - 'completed': Has completed form -> thank you message
    """
    if is_first_time_user(user_id):
        return 'first_time'
    if has_completed_form(user_id):
        return 'completed'
    user = get_user(user_id)
    if not user or user.get('form_status') != 'pending':
        return 'completed'
    message_count = get_user_message_count(user_id)
    if message_count == 1:
        return 'second_interaction'
    return 'follow_up'

def mark_follow_up_sent(user_id):
    """Mark that follow-up message was sent"""
    sheets = get_sheets_service()
    return sheets.mark_follow_up_sent(user_id)
    
def increment_message_count(user_id):
    """
    Update last_follow_up_sent for second interaction.
    For subsequent interactions, rely on time comparison in get_user_stage.
    """
    user = get_user(user_id)
    if user and not user.get('last_follow_up_sent'):
        mark_follow_up_sent(user_id)

def get_welcome_message(user_name=DEFAULT_USER_NAME):
    """Get welcome message using template"""
    return get_welcome_template_message(user_name)

def get_form_message(user_name=DEFAULT_USER_NAME):
    """Get customer care form message using template"""
    return get_customercare_template_message(user_name, FORM_URL)

def get_after_interaction_message(user_name=DEFAULT_USER_NAME):
    """Get reminder message after user interaction using template"""
    return get_reminder_template_message(user_name, FORM_URL)