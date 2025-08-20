"""
FastAPI Dependencies - Dependency injection for services

Usage in endpoints:
    from fastapi import Depends
    from core.deps import get_form_service
    
    @router.post("/webhook")
    async def webhook(form_service: FormService = Depends(get_form_service)):
        user = form_service.get_user(user_id)
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from services.bot_service import BotService
from services.form_service import FormService
from services.template_service import TemplateService
from services.google_sheets_service import GoogleSheetsService
from core.config import settings


@lru_cache()
def get_google_sheets_service() -> GoogleSheetsService:
    """Get GoogleSheetsService singleton instance"""
    return GoogleSheetsService()


@lru_cache() 
def get_template_service() -> TemplateService:
    """Get TemplateService singleton instance"""
    return TemplateService()


@lru_cache()
def get_form_service(
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service),
    template_service: TemplateService = Depends(get_template_service)
) -> FormService:
    """Get FormService with injected dependencies"""
    return FormService(sheets_service=sheets_service, template_service=template_service)


@lru_cache()
def get_bot_service(
    form_service: FormService = Depends(get_form_service)
) -> BotService:
    """Get BotService with injected dependencies"""
    return BotService(form_service=form_service)


# Type annotations for easier usage
GoogleSheetsServiceDep = Annotated[GoogleSheetsService, Depends(get_google_sheets_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
FormServiceDep = Annotated[FormService, Depends(get_form_service)]
BotServiceDep = Annotated[BotService, Depends(get_bot_service)]
