import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def load_template(template_name):
    """Load template JSON file"""
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", f"{template_name}.json")
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template {template_name} not found")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in template {template_name}")

def format_template_message(template_data, user_name="Bạn", survey_link=None):
    """Format template message with user data"""
    # Get text from body
    message_text = ""
    for body_item in template_data.get("body", []):
        if body_item["type"] == "text":
            text = body_item["text"]
            # Replace placeholders
            text = text.replace("<user_name>", user_name)
            if survey_link:
                text = text.replace("<survey_link>", survey_link)
            message_text += text
    
    return message_text

def create_keyboard_from_template(template_data, survey_link=None):
    """Create inline keyboard from template CTAs"""
    ctas = template_data.get("ctas", [])
    if not ctas:
        return None
    
    buttons = []
    for cta in ctas:
        if cta["type"] == "url":
            url = cta["url"]
            if survey_link and "<survey_link>" in url:
                url = url.replace("<survey_link>", survey_link)
            buttons.append([InlineKeyboardButton(cta["name"], url=url)])
        # Có thể thêm các loại CTA khác ở đây
    
    # Thêm button "Tôi đã điền form" cho các template có form
    if any("form" in template_data.get("template_name", "").lower() or 
           "survey" in template_data.get("template_name", "").lower() or
           "khảo sát" in template_data.get("template_name", "").lower()
           for _ in [1]):
        buttons.append([InlineKeyboardButton("Tôi đã điền form", callback_data="form_filled")])
    
    return InlineKeyboardMarkup(buttons) if buttons else None

def get_welcome_template_message(user_name="Bạn"):
    """Get welcome message from template_welcome_1"""
    template = load_template("template_welcome_1")
    text = format_template_message(template, user_name)
    
    # Thêm button "Bắt đầu" cho welcome message
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bắt đầu", callback_data="welcome_start")]
    ])
    
    return text, kb

def get_customercare_template_message(user_name="Bạn", survey_link=None):
    """Get customer care message from template_customercare_2"""
    template = load_template("template_customercare_2")
    text = format_template_message(template, user_name, survey_link)
    kb = create_keyboard_from_template(template, survey_link)
    
    return text, kb

def get_reminder_template_message(user_name="Bạn", survey_link=None):
    """Get reminder message from template_customercare_3"""
    template = load_template("template_customercare_3")
    text = format_template_message(template, user_name, survey_link)
    kb = create_keyboard_from_template(template, survey_link)
    
    return text, kb
