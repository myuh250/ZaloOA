import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

class TemplateService:
    """Service to handle message templates"""
    
    def __init__(self, templates_dir: str = None):
        """Initialize template service
        
        Args:
            templates_dir: Path to templates directory, defaults to ../templates
        """
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)
    
    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template JSON file"""
        template_path = self.templates_dir / f"{template_name}.json"
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Template {template_name} not found at {template_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in template {template_name}: {e}")

    def format_template_message(self, template_data: Dict[str, Any], 
                                user_name: str = "Bạn", 
                                survey_link: str = None,
                                embed_links: bool = True,
                                add_callback_instructions: bool = True) -> str:
        """Format template message with user data
        
        Args:
            template_data: Template data from JSON
            user_name: User name to replace in template
            survey_link: Survey link to replace in template
            embed_links: If True, embed CTA URLs directly into text instead of using buttons
            add_callback_instructions: If True, add callback instructions for form completion
        """
        message_text = ""
        for body_item in template_data.get("body", []):
            if body_item.get("type") == "text":
                text = body_item["text"]
                # Replace placeholders
                text = text.replace("<user_name>", user_name)
                if survey_link:
                    text = text.replace("<survey_link>", survey_link)
                message_text += text
        
        # If embed_links is True, append CTA links to the message text
        if embed_links:
            ctas = template_data.get("ctas", [])
            for cta in ctas:
                if cta.get("type") == "url":
                    url = cta["url"]
                    if survey_link and "<survey_link>" in url:
                        url = url.replace("<survey_link>", survey_link)
                    # Append link to message with proper formatting
                    link_text = f"\n\n👉 {['name']}: {url}"
                    message_text += link_text
        
        # Add callback instructions for form templates instead of buttons
        if add_callback_instructions:
            template_name = template_data.get("template_name", "").lower()
            if any(keyword in template_name for keyword in ["form", "survey", "khảo sát"]):
                message_text += '\n\nNếu bạn đã hoàn thành form, vui lòng nhắn "tôi đã điền form" để chúng tôi ghi nhận.'
        
        return message_text

    def create_buttons_from_template(self, template_data: Dict[str, Any], 
                                     survey_link: str = None) -> List[Dict[str, Any]]:
        """Create platform-agnostic buttons from template CTAs
        
        Returns:
            List of button dictionaries with 'text', 'type', and 'data'/'url' keys
        """
        ctas = template_data.get("ctas", [])
        buttons = []
        
        for cta in ctas:
            if cta.get("type") == "url":
                url = cta["url"]
                if survey_link and "<survey_link>" in url:
                    url = url.replace("<survey_link>", survey_link)
                buttons.append({
                    "text": cta["name"],
                    "type": "url",
                    "url": url
                })
        
        # Add form completion button for form templates
        template_name = template_data.get("template_name", "").lower()
        if any(keyword in template_name for keyword in ["form", "survey", "khảo sát"]):
            buttons.append({
                "text": "Tôi đã điền form",
                "type": "callback",
                "data": "form_filled"
            })
        
        return buttons

    def get_welcome_message(self, user_name: str = "Bạn") -> Tuple[str, List[Dict[str, Any]]]:
        """Get welcome message from template_welcome_1"""
        template = self.load_template("template_welcome_1")
        text = self.format_template_message(template, user_name, embed_links=False, add_callback_instructions=False)
        
        # No buttons for Zalo - all interactions via text
        buttons = []
        
        return text, buttons

    def get_customercare_message(self, user_name: str = "Bạn", 
                                 survey_link: str = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Get customer care message from template_customercare_2"""
        template = self.load_template("template_customercare_2")
        text = self.format_template_message(template, user_name, survey_link, embed_links=True, add_callback_instructions=True)
        
        # No buttons for Zalo - callback instructions are embedded in text
        buttons = []
        
        return text, buttons

    def get_reminder_message(self, user_name: str = "Bạn", 
                            survey_link: str = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Get reminder message from template_customercare_3"""
        template = self.load_template("template_customercare_3")
        text = self.format_template_message(template, user_name, survey_link, embed_links=True, add_callback_instructions=True)
        
        # No buttons for Zalo - callback instructions are embedded in text
        buttons = []
        
        return text, buttons


# Global instance for backward compatibility  
_template_service = None

def get_template_service() -> TemplateService:
    """Get TemplateService singleton instance"""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service

# Backward compatibility: Keep minimal functions for legacy support
def load_template(template_name: str):
    """DEPRECATED: Use TemplateService.load_template() instead"""
    return get_template_service().load_template(template_name)
