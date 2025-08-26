from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os
from pathlib import Path
from openai import OpenAI

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Bot Configuration
    bot_token: str
    bot_username: Optional[str] = None 
    form_url: str
    
    # Zalo Configuration
    zalo_oa_access_token: Optional[str] = None
    zalo_oa_refresh_token: Optional[str] = None
    zalo_app_id: Optional[str] = None
    zalo_secret_key: Optional[str] = None  
    
    # Google Sheets
    google_sheet_id: Optional[str] = None
    google_sheet_name: str = "ZaloOA Users"
    worksheet_name: str = "UserStatus"
    credentials_file: str = "credentials.json"
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-southeast-1"
    aws_default_region: str = "ap-southeast-1"  
    cloudwatch_log_group: str = "MyFastAPIAppLogs"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-nano"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 150
    openai_timeout: int = 30
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Application
    app_name: str = "Zalo OA Bot API"
    app_version: str = "1.0.0"
    
    # Render.com specific
    render_service_id: Optional[str] = None
    render_api_key: Optional[str] = None
    
    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v):
        if not v or v.strip() == "":
            raise ValueError('BOT_TOKEN is required and cannot be empty')
        return v.strip()
    
    @field_validator('form_url')
    @classmethod
    def validate_form_url(cls, v):
        if not v or v.strip() == "":
            raise ValueError('FORM_URL is required and cannot be empty')
        return v.strip()
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

# Global settings instance
settings = Settings()