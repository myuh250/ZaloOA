from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from services.bot_service import BotService
from services.form_service import FormService
from services.template_service import TemplateService
from services.google_sheets_service import GoogleSheetsService
from core.config import settings
from core.usecases.message_usecase import MessageUseCase
from core.usecases.form_sync_usecase import FormSyncUseCase
from core.usecases.status_change_usecase import StatusChangeUseCase
from workers.background import BackgroundTaskManager
from adapters.zalo_messaging_gateway import ZaloMessagingGateway
import os


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


@lru_cache()
def get_zalo_gateway() -> ZaloMessagingGateway:
    """Get ZaloMessagingGateway with access token"""
    access_token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    return ZaloMessagingGateway(access_token=access_token)


@lru_cache()
def get_message_usecase(
    bot_service: BotService = Depends(get_bot_service),
    zalo_gateway: ZaloMessagingGateway = Depends(get_zalo_gateway)
) -> MessageUseCase:
    """Get MessageUseCase with injected dependencies"""
    return MessageUseCase(bot_service=bot_service, message_gateway=zalo_gateway)


def get_form_sync_usecase() -> FormSyncUseCase:
    return FormSyncUseCase()


def get_status_change_usecase(
    bot_service: BotService = Depends(get_bot_service),
    zalo_gateway: ZaloMessagingGateway = Depends(get_zalo_gateway)
) -> StatusChangeUseCase:
    return StatusChangeUseCase(bot_service=bot_service, gateway=zalo_gateway)


def get_background_manager() -> BackgroundTaskManager:
    return BackgroundTaskManager()



# Type annotations for easier usage
GoogleSheetsServiceDep = Annotated[GoogleSheetsService, Depends(get_google_sheets_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
FormServiceDep = Annotated[FormService, Depends(get_form_service)]
BotServiceDep = Annotated[BotService, Depends(get_bot_service)]
MessageUseCaseDep = Annotated[MessageUseCase, Depends(get_message_usecase)]
FormSyncUseCaseDep = Annotated[FormSyncUseCase, Depends(get_form_sync_usecase)]
StatusChangeUseCaseDep = Annotated[StatusChangeUseCase, Depends(get_status_change_usecase)]
