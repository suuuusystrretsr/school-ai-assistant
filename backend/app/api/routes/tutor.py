from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User, UserProfile
from app.schemas.tutor import TutorChatRequest, TutorChatResponse
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/tutor', tags=['tutor'])
ai = get_ai_provider()


@router.post('/chat', response_model=TutorChatResponse)
def tutor_chat(payload: TutorChatRequest, user: User = Depends(get_current_user)):
    grade_level = None
    if isinstance(user.profile, UserProfile) and user.profile.grade_level:
        grade_level = user.profile.grade_level

    prompt = payload.message
    if grade_level:
        prompt = f'[Student grade: {grade_level}] {payload.message}'

    result = ai.tutor_chat(prompt, payload.subject, payload.mode)
    if grade_level:
        result['reply'] = f'Calibrated for {grade_level}. {result["reply"]}'

    return TutorChatResponse(**result)
