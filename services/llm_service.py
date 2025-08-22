import json
import logging
from openai import OpenAI
from typing import Optional, Dict, List, Any
from core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Centralized service for all interacting with LLMs"""
    
    def __init__(self):
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured. LLM operations will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            self.temperature = settings.openai_temperature
            self.max_tokens = settings.openai_max_tokens
            
    def _is_available(self) -> bool:
        """Check if LLM is available"""
        return self.client is not None
    
    def extract_email(self, text: str) -> Dict[str, Any]:
        """Extract email from text using LLM"""
        if not self._is_available():
            return {"email": None, "confidence": 0.0, "error": "LLM not configured"}
        
        prompt = f"""
        From the following message, extract EMAIL:
        "{text}"

        Rules:
        - Email: must be in a valid format with @ and domain
        - If not found, return null

        Return in strict JSON format:
        {{"email": "email or null"}}

        Examples:
        - "nguyễn văn a test@gmail.com" → {{"name": "nguyễn văn a", "email": "test@gmail.com"}}
        - "minh, minh123@yahoo.com" → {{"name": "minh", "email": "minh123@yahoo.com"}}
        - "chỉ có email@domain.com thôi" → {{"name": null, "email": "email@domain.com"}}
        """
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
            
        content = response.choices[0].message.content.strip()
            
        extracted = json.loads(content)
        email = extracted.get("email", None)
                
        if email and isinstance(email, str):
            email = email.strip().lower()
            if "@" not in email or "." not in email.split("@")[1]:
                email = None

        result = {
            "email": email
        }
            
        logger.info(f"Extracted: {result}")
        return result
        
_llm_service = None

def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service