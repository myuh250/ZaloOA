from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from workers.follow_up_cron import run_sync_form_responses


class FormSubmittedDTO(BaseModel):
    email: Optional[str] = None
    form_id: Optional[str] = None
    timestamp: Optional[str] = None


class FormSyncUseCase:
    async def run_sync(self, dto: FormSubmittedDTO) -> Dict[str, Any]:
        """Trigger form responses sync when a new submission is received."""
        email = (dto.email or "").strip().lower()
        if not email:
            return {"status": "ignored", "message": "No email provided"}

        updated_users = await run_sync_form_responses()
        return {
            "status": "success",
            "processed": len(updated_users)
        }


