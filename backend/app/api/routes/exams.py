from datetime import datetime, timezone
from statistics import mean

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.exam import ExamQuestion, ExamSimulation
from app.models.user import User
from app.schemas.exam import ExamGenerateRequest, ExamGenerateResponse, ExamQuestionReview, ExamResultResponse, ExamSubmitRequest

router = APIRouter(prefix='/exams', tags=['exams'])


STYLE_LIBRARY = {
    'strict teacher': 'strict grading, precision, and minimal partial credit',
    'tricky teacher': 'distractors that look correct unless reasoning is careful',
    'short-answer teacher': 'concise recall and exact wording',
    'reasoning-heavy teacher': 'explain why, not only what',
    'exam-board style': 'balanced conceptual + applied test style',
    'custom': 'custom teacher style from user prompt',
}


def _effective_style(payload: ExamGenerateRequest) -> str:
    if payload.teacher_style.lower() == 'custom' and payload.custom_teacher_style and payload.custom_teacher_style.strip():
        return payload.custom_teacher_style.strip()
    return payload.teacher_style


def _effective_topic(payload: ExamGenerateRequest) -> str:
    if payload.topic and payload.topic.strip():
        return payload.topic.strip()
    return payload.subject


def _difficulty_signal(difficulty: str) -> str:
    d = difficulty.lower().strip()
    if d == 'easy':
        return 'foundation-level'
    if d == 'hard':
        return 'advanced-level'
    return 'standard-level'


def _question_pattern(subject: str, topic: str, difficulty: str, style: str, idx: int) -> dict:
    level = _difficulty_signal(difficulty)
    style_hint = STYLE_LIBRARY.get(style.lower(), style)
    pattern = idx % 5

    if pattern == 0:
        return {
            'prompt': f'[{style}] {topic}: Which statement is the strongest {level} explanation?',
            'choices': [
                f'{topic} should be solved by memorizing random facts only.',
                f'{topic} should begin by identifying knowns, unknowns, and constraints.',
                f'{topic} never needs checking after solving.',
                f'{topic} is unrelated to {subject.lower()} reasoning.',
            ],
            'correct_answer': 'B',
            'explanation': f'The best first move is a structured setup. This matches {style_hint}.',
        }

    if pattern == 1:
        return {
            'prompt': f'[{style}] In {subject}, what is the best first step for a {topic} problem?',
            'choices': [
                'List the givens and goal before choosing a method.',
                'Skip setup and jump directly to final answer.',
                'Avoid evidence/units checks to save time.',
                'Use a method that ignores the question wording.',
            ],
            'correct_answer': 'A',
            'explanation': 'Strong setup prevents logic drift and reduces avoidable mistakes.',
        }

    if pattern == 2:
        return {
            'prompt': f'[{style}] Which mistake most often lowers {topic} scores?',
            'choices': [
                'Adding a quick self-check at the end.',
                'Annotating assumptions before solving.',
                'Applying rules without verifying if conditions match.',
                'Explaining reasoning in one sentence.',
            ],
            'correct_answer': 'C',
            'explanation': 'Rule misuse without condition checking is a high-frequency score killer.',
        }

    if pattern == 3:
        return {
            'prompt': f'[{style}] A student is stuck on {topic}. What action is most productive next?',
            'choices': [
                'Retry the exact same approach repeatedly.',
                'Switch topics immediately and never return.',
                'Find the missing prerequisite and do one targeted drill.',
                'Wait and hope the answer appears.',
            ],
            'correct_answer': 'C',
            'explanation': 'Targeted prerequisite repair resolves root-cause gaps fastest.',
        }

    return {
        'prompt': f'[{style}] Which review strategy best improves retention for {topic}?',
        'choices': [
            'Read once and never revisit.',
            'Only do easiest questions repeatedly.',
            'Skip spaced review to save effort.',
            'Use spaced recall + mixed application practice.',
        ],
        'correct_answer': 'D',
        'explanation': 'Spaced recall plus mixed practice gives stronger long-term retention.',
    }


def _build_question_bank(subject: str, topic: str, difficulty: str, style: str, question_count: int) -> list[dict]:
    return [_question_pattern(subject, topic, difficulty, style, idx) for idx in range(question_count)]


def _predict_score(user_id: int, db: Session) -> int:
    previous_scores = [
        row.actual_score
        for row in db.query(ExamSimulation).filter(ExamSimulation.user_id == user_id, ExamSimulation.actual_score.isnot(None)).all()
        if row.actual_score is not None
    ]
    if not previous_scores:
        return 0
    return int(round(sum(previous_scores) / len(previous_scores)))


@router.post('/generate', response_model=ExamGenerateResponse)
def generate_exam(payload: ExamGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    predicted = _predict_score(user.id, db)
    style = _effective_style(payload)
    topic = _effective_topic(payload)

    exam = ExamSimulation(
        user_id=user.id,
        subject=payload.subject,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        started_at=datetime.now(timezone.utc),
        predicted_score=predicted,
    )
    db.add(exam)
    db.flush()

    questions: list[dict] = []
    for item in _build_question_bank(payload.subject, topic, payload.difficulty, style, payload.question_count):
        q = ExamQuestion(
            exam_id=exam.id,
            prompt=item['prompt'],
            choices=item['choices'],
            correct_answer=item['correct_answer'],
            explanation=item['explanation'],
        )
        db.add(q)
        db.flush()
        questions.append({'id': q.id, 'prompt': q.prompt, 'choices': q.choices})

    db.commit()

    return ExamGenerateResponse(
        exam_id=exam.id,
        subject=payload.subject,
        topic=topic,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        question_count=payload.question_count,
        teacher_style=style,
        predicted_score=predicted,
        questions=questions,
    )


@router.post('/{exam_id}/submit', response_model=ExamResultResponse)
def submit_exam(exam_id: int, payload: ExamSubmitRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = db.get(ExamSimulation, exam_id)
    if not exam or exam.user_id != user.id:
        raise HTTPException(status_code=404, detail='Exam not found')

    questions = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).all()
    if not questions:
        raise HTTPException(status_code=404, detail='No questions found for this exam')

    submitted_answers = {int(key): value for key, value in payload.answers.items()}

    correct_count = 0
    weak_areas: list[str] = []
    reviews: list[ExamQuestionReview] = []

    for q in questions:
        selected = submitted_answers.get(q.id)
        is_correct = selected == q.correct_answer
        if is_correct:
            correct_count += 1
        else:
            weak_areas.append(q.prompt)

        reviews.append(
            ExamQuestionReview(
                question_id=q.id,
                prompt=q.prompt,
                choices=q.choices,
                selected_answer=selected,
                correct_answer=q.correct_answer,
                is_correct=is_correct,
                explanation=q.explanation,
            )
        )

    total = len(questions)
    score = int(round((correct_count / total) * 100)) if total else 0

    confidence_values = []
    if payload.confidence_by_question:
        confidence_values = [max(0, min(100, int(value))) for value in payload.confidence_by_question.values()]
    avg_confidence = int(round(mean(confidence_values))) if confidence_values else score
    confidence_gap = avg_confidence - score

    exam.actual_score = score
    exam.completed_at = datetime.now(timezone.utc)
    exam.weak_areas = weak_areas[:3] if weak_areas else ['No major weak areas']
    db.add(exam)
    db.commit()

    next_topics = [
        'Target one weak area with a short drill set',
        'Run a timed mixed mini-quiz',
        'Review errors with spaced recall in 24h',
    ]

    wrong_count = total - correct_count
    outcome_simulation = {
        'if_exam_today': score,
        'if_study_30_more_minutes': min(100, score + 6 + max(0, 2 - (wrong_count // 3))),
        'if_fix_one_weak_area': min(100, score + (12 if wrong_count else 4)),
        'if_ignore_retention_risk': max(0, score - (8 if wrong_count else 4)),
    }

    return ExamResultResponse(
        exam_id=exam.id,
        actual_score=score,
        weak_areas=exam.weak_areas,
        next_topics=next_topics,
        reviews=reviews,
        confidence_gap=confidence_gap,
        outcome_simulation=outcome_simulation,
    )
