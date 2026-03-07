from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.exam import ExamQuestion, ExamSimulation
from app.models.user import User
from app.schemas.exam import ExamGenerateRequest, ExamGenerateResponse, ExamResultResponse, ExamSubmitRequest

router = APIRouter(prefix='/exams', tags=['exams'])


@router.post('/generate', response_model=ExamGenerateResponse)
def generate_exam(payload: ExamGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = ExamSimulation(
        user_id=user.id,
        subject=payload.subject,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        started_at=datetime.now(timezone.utc),
        predicted_score=72 if payload.difficulty == 'medium' else 64,
    )
    db.add(exam)
    db.flush()

    questions: list[dict] = []
    for idx in range(1, 11):
        correct = 'B' if idx % 2 == 0 else 'C'
        q = ExamQuestion(
            exam_id=exam.id,
            prompt=f'{payload.subject} question {idx} ({payload.difficulty})',
            choices=['A', 'B', 'C', 'D'],
            correct_answer=correct,
            explanation=f'Explanation for question {idx}.',
        )
        db.add(q)
        questions.append({'id': idx, 'prompt': q.prompt, 'choices': q.choices})

    db.commit()
    return ExamGenerateResponse(
        exam_id=exam.id,
        subject=exam.subject,
        difficulty=exam.difficulty,
        duration_minutes=exam.duration_minutes,
        predicted_score=exam.predicted_score,
        questions=questions,
    )


@router.post('/{exam_id}/submit', response_model=ExamResultResponse)
def submit_exam(exam_id: int, payload: ExamSubmitRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = db.get(ExamSimulation, exam_id)
    if not exam or exam.user_id != user.id:
        raise HTTPException(status_code=404, detail='Exam not found')

    questions = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).all()
    if not questions:
        raise HTTPException(status_code=404, detail='No questions for exam')

    correct_count = 0
    for q in questions:
        user_answer = payload.answers.get(q.id)
        if user_answer == q.correct_answer:
            correct_count += 1

    score = int((correct_count / len(questions)) * 100)
    exam.actual_score = score
    exam.completed_at = datetime.now(timezone.utc)
    exam.weak_areas = ['Topic A', 'Topic B'] if score < 75 else ['Time management']
    db.add(exam)
    db.commit()

    return ExamResultResponse(
        exam_id=exam.id,
        actual_score=score,
        weak_areas=exam.weak_areas,
        next_topics=['Review weak areas', 'Timed mixed quiz', 'Spaced recall set'],
    )
