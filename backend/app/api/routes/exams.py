from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.exam import ExamQuestion, ExamSimulation
from app.models.user import User
from app.schemas.exam import ExamGenerateRequest, ExamGenerateResponse, ExamResultResponse, ExamSubmitRequest

router = APIRouter(prefix='/exams', tags=['exams'])


def _build_question_bank(subject: str, difficulty: str) -> list[dict]:
    s = subject.lower().strip()
    if s == 'math':
        return [
            {
                'prompt': 'Solve: 2x + 8 = 20',
                'choices': ['x = 6', 'x = 8', 'x = 4', 'x = 2'],
                'correct_answer': 'A',
                'explanation': 'Subtract 8 from both sides, then divide by 2.',
            },
            {
                'prompt': 'What is the slope of the line y = 3x - 5?',
                'choices': ['-5', '3', '5', '0'],
                'correct_answer': 'B',
                'explanation': 'In y = mx + b, slope m is 3.',
            },
            {
                'prompt': 'Factor: x^2 - 9',
                'choices': ['(x - 3)(x + 3)', '(x - 9)(x + 1)', '(x - 3)^2', 'Prime'],
                'correct_answer': 'A',
                'explanation': 'Difference of squares: a^2 - b^2 = (a-b)(a+b).',
            },
            {
                'prompt': 'Evaluate 5(2 + 3)',
                'choices': ['10', '15', '25', '13'],
                'correct_answer': 'C',
                'explanation': 'Parentheses first: 2+3=5, then 5*5=25.',
            },
            {
                'prompt': 'Which is equivalent to 3/4?',
                'choices': ['6/10', '9/12', '12/20', '15/24'],
                'correct_answer': 'B',
                'explanation': 'Multiply numerator and denominator by 3: 3/4 = 9/12.',
            },
        ]

    if s == 'biology':
        return [
            {
                'prompt': 'Primary site of photosynthesis in plant cells?',
                'choices': ['Nucleus', 'Mitochondria', 'Chloroplast', 'Ribosome'],
                'correct_answer': 'C',
                'explanation': 'Photosynthesis occurs in chloroplasts.',
            },
            {
                'prompt': 'What carries oxygen in blood?',
                'choices': ['Platelets', 'Hemoglobin', 'Plasma only', 'White blood cells'],
                'correct_answer': 'B',
                'explanation': 'Hemoglobin in red blood cells binds oxygen.',
            },
            {
                'prompt': 'DNA is found mainly in the...',
                'choices': ['Cell membrane', 'Nucleus', 'Cytoplasm only', 'Golgi body'],
                'correct_answer': 'B',
                'explanation': 'In eukaryotes, DNA is primarily in the nucleus.',
            },
            {
                'prompt': 'Which process produces ATP in mitochondria?',
                'choices': ['Photosynthesis', 'Cellular respiration', 'Diffusion', 'Transcription'],
                'correct_answer': 'B',
                'explanation': 'Cellular respiration in mitochondria produces ATP.',
            },
            {
                'prompt': 'Basic unit of life?',
                'choices': ['Atom', 'Cell', 'Tissue', 'Organ'],
                'correct_answer': 'B',
                'explanation': 'The cell is the fundamental unit of life.',
            },
        ]

    return [
        {
            'prompt': f'{subject} question {idx} ({difficulty})',
            'choices': ['A', 'B', 'C', 'D'],
            'correct_answer': 'B' if idx % 2 == 0 else 'C',
            'explanation': f'Explanation for {subject} question {idx}.',
        }
        for idx in range(1, 6)
    ]


@router.post('/generate', response_model=ExamGenerateResponse)
def generate_exam(payload: ExamGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    previous_scores = [
        row.actual_score
        for row in db.query(ExamSimulation).filter(ExamSimulation.user_id == user.id, ExamSimulation.actual_score.isnot(None)).all()
        if row.actual_score is not None
    ]
    predicted = int(sum(previous_scores) / len(previous_scores)) if previous_scores else 0

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
    for item in _build_question_bank(payload.subject, payload.difficulty):
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

    submitted_answers = {int(key): value for key, value in payload.answers.items()}

    correct_count = 0
    weak_prompts: list[str] = []
    for q in questions:
        user_answer = submitted_answers.get(q.id)
        if user_answer == q.correct_answer:
            correct_count += 1
        else:
            weak_prompts.append(q.prompt)

    score = int((correct_count / len(questions)) * 100)
    exam.actual_score = score
    exam.completed_at = datetime.now(timezone.utc)
    exam.weak_areas = weak_prompts[:3] if weak_prompts else ['No major weak areas']
    db.add(exam)
    db.commit()

    next_topics = [
        'Review incorrect questions',
        'Practice a mixed timed set',
        'Spaced recall tomorrow',
    ]

    return ExamResultResponse(
        exam_id=exam.id,
        actual_score=score,
        weak_areas=exam.weak_areas,
        next_topics=next_topics,
    )
