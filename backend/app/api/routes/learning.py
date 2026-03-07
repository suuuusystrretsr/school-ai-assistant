
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.schemas.learning import (
    ExplainMistakeRequest,
    ExplainMistakeResponse,
    GapScanResponse,
    LectureSummarizeRequest,
    LectureSummarizeResponse,
    LearningStyleResponse,
    MistakePatternResponse,
)
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/learning', tags=['learning'])
ai = get_ai_provider()


@router.post('/lecture-summarize', response_model=LectureSummarizeResponse)
def lecture_summarize(payload: LectureSummarizeRequest, user: User = Depends(get_current_user)):
    result = ai.summarize_lecture(payload.content)
    return LectureSummarizeResponse(**result)


@router.post('/explain-mistake', response_model=ExplainMistakeResponse)
def explain_mistake(payload: ExplainMistakeRequest, user: User = Depends(get_current_user)):
    result = ai.analyze_mistake(payload.question, payload.user_answer, payload.correct_answer)
    return ExplainMistakeResponse(**result)


@router.get('/style', response_model=LearningStyleResponse)
def detect_learning_style(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    telemetry = {'practice_completed': 9, 'videos_watched': 4, 'explanation_reads': 12}
    style = ai.detect_learning_style(telemetry)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if profile:
        profile.preferred_learning_style = style['style']
        db.add(profile)
        db.commit()

    return style


@router.get('/mistake-patterns', response_model=MistakePatternResponse)
def detect_mistake_patterns(user: User = Depends(get_current_user)):
    return MistakePatternResponse(
        patterns=['Sign mistakes', 'Skipping intermediate algebra steps'],
        correction_drills=[
            {'title': 'Sign Discipline Drill', 'questions': 8},
            {'title': 'Step Completion Drill', 'questions': 6},
        ],
        focused_practice=[
            {'topic': 'Algebra simplification', 'difficulty': 'easy'},
            {'topic': 'Equation balancing', 'difficulty': 'medium'},
        ],
    )


@router.get('/gap-scan', response_model=GapScanResponse)
def gap_scan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    weak_topics = profile.weak_topics if profile else ['calculus derivatives']
    result = ai.scan_knowledge_gaps({'weak_topics': weak_topics})
    return GapScanResponse(**result)
