import logging


logger = logging.getLogger(__name__)


async def process_message_background(message_usecase, process_request):
    """Process message in background to keep webhook response fast."""
    try:
        result = await message_usecase.process_message(process_request)
        if not result.success:
            logger.error(f"Background processing failed: {result.message}")
    except Exception as e:
        logger.error(f"Background processing error: {e}")


