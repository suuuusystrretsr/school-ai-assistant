from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.tutor import TutorChatRequest, TutorChatResponse
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/tutor', tags=['tutor'])
ai = get_ai_provider()


@router.post('/chat', response_model=TutorChatResponse)
def tutor_chat(payload: TutorChatRequest, user: User = Depends(get_current_user)):
    result = ai.tutor_chat(payload.message, payload.subject, payload.mode)
    return TutorChatResponse(**result)
