from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.homework import GeneratedSolution, HomeworkRequest, PracticeSet
from app.models.user import User
from app.schemas.homework import HomeworkSolveRequest, HomeworkSolveResponse, PracticeGenerateRequest, PracticeSetResponse, WhiteboardPayload
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/homework', tags=['homework'])
ai = get_ai_provider()


@router.post('/solve', response_model=HomeworkSolveResponse)
def solve_homework(payload: HomeworkSolveRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    request_row = HomeworkRequest(
        user_id=user.id,
        question_text=payload.question_text,
        source_type='text',
        explanation_mode=payload.explanation_mode,
    )
    db.add(request_row)
    db.flush()

    result = ai.solve_problem(payload.question_text, payload.explanation_mode)
    solution = GeneratedSolution(
        homework_request_id=request_row.id,
        final_answer=result['final_answer'],
        steps=result['steps'],
        simplified_explanation=result['explanations']['eli5'],
        advanced_explanation=result['explanations']['advanced'],
        teacher_mode_explanation=result['explanations']['teacher'],
        confidence_score=result['confidence_score'],
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)

    return HomeworkSolveResponse(
        request_id=request_row.id,
        solution_id=solution.id,
        final_answer=solution.final_answer,
        steps=solution.steps,
        explanation_by_mode=result['explanations'],
    )


@router.post('/solve-with-files', response_model=HomeworkSolveResponse)
async def solve_with_files(
    question_text: str = Form(...),
    explanation_mode: str = Form('normal'),
    files: list[UploadFile] = File(default=[]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request_row = HomeworkRequest(
        user_id=user.id,
        question_text=question_text,
        source_type='upload',
        attachment_urls=[f.filename for f in files],
        explanation_mode=explanation_mode,
    )
    db.add(request_row)
    db.flush()

    result = ai.solve_problem(question_text, explanation_mode)
    solution = GeneratedSolution(
        homework_request_id=request_row.id,
        final_answer=result['final_answer'],
        steps=result['steps'],
        simplified_explanation=result['explanations']['eli5'],
        advanced_explanation=result['explanations']['advanced'],
        teacher_mode_explanation=result['explanations']['teacher'],
        confidence_score=result['confidence_score'],
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)

    return HomeworkSolveResponse(
        request_id=request_row.id,
        solution_id=solution.id,
        final_answer=solution.final_answer,
        steps=solution.steps,
        explanation_by_mode=result['explanations'],
    )


@router.post('/practice', response_model=PracticeSetResponse)
def generate_practice(payload: PracticeGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.get(GeneratedSolution, payload.source_solution_id)
    if not source:
        raise HTTPException(status_code=404, detail='Source solution not found')

    result = ai.generate_practice(source.final_answer, payload.difficulty)
    practice = PracticeSet(
        user_id=user.id,
        source_solution_id=source.id,
        title=result['title'],
        difficulty=payload.difficulty,
        questions=result['questions'],
        answer_key=result['answer_key'],
        worked_solutions=result['worked_solutions'],
    )
    db.add(practice)
    db.commit()
    db.refresh(practice)
    return practice


@router.post('/whiteboard-solve')
def whiteboard_solver_placeholder(payload: WhiteboardPayload, user: User = Depends(get_current_user)):
    hints = ai.generate_hints('whiteboard equation payload')
    return {
        'status': 'placeholder',
        'message': 'Whiteboard stroke capture accepted. Handwriting recognition is pluggable for next phase.',
        'stroke_count': len(payload.strokes),
        'next': 'Integrate OCR/math parser service for handwritten equations.',
        'hints': hints,
    }


@router.get('/hints/{homework_request_id}')
def get_progressive_hints(homework_request_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.get(HomeworkRequest, homework_request_id)
    if not req or req.user_id != user.id:
        raise HTTPException(status_code=404, detail='Homework request not found')
    return {'hints': ai.generate_hints(req.question_text)}
