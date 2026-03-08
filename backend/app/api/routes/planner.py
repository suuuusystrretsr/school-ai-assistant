from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.planner import PlannerTask
from app.models.user import User, UserProfile
from app.schemas.planner import PlannerGenerateRequest, PlannerTaskResponse
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/planner', tags=['planner'])
ai = get_ai_provider()


@router.post('/generate', response_model=list[PlannerTaskResponse])
def generate_plan(payload: PlannerGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    grade_level = None
    if isinstance(user.profile, UserProfile) and user.profile.grade_level:
        grade_level = user.profile.grade_level

    payload_data = payload.model_dump()
    if grade_level:
        payload_data['grade_level'] = grade_level

    generated_tasks = ai.generate_study_plan(payload_data)
    rows: list[PlannerTask] = []
    for item in generated_tasks:
        row = PlannerTask(
            user_id=user.id,
            subject=item['subject'],
            topic=item['topic'],
            due_date=date.fromisoformat(item['due_date']),
            minutes=item['minutes'],
            priority=item['priority'],
            task_type=item['task_type'],
            recommendations=(item['recommendations'] + [f'Calibrated for {grade_level}']) if grade_level else item['recommendations'],
            completed=False,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


@router.get('/tasks', response_model=list[PlannerTaskResponse])
def get_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(PlannerTask).filter(PlannerTask.user_id == user.id).order_by(PlannerTask.due_date.asc()).all()
