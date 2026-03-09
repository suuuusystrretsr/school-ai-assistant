from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.classroom import ClassroomSession
from app.models.session_signal import SessionSignal
from app.models.user import User
from app.schemas.classroom import (
    ClassroomEndRequest,
    ClassroomHistoryResponse,
    ClassroomRespondRequest,
    ClassroomSessionSummary,
    ClassroomStartRequest,
    ClassroomStateResponse,
)
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix='/classroom', tags=['classroom'])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _compact_marker() -> dict:
    return {
        'role': 'system',
        'kind': 'transcript_compacted',
        'message': 'Transcript compacted to summary for older sessions.',
        'timestamp': _iso(_now()),
    }


def _is_compacted(transcript: list[dict] | None) -> bool:
    if not transcript:
        return False
    first = transcript[0] if isinstance(transcript[0], dict) else {}
    return first.get('kind') == 'transcript_compacted'


def _last_teacher_turn(transcript: list[dict]) -> dict:
    for item in reversed(transcript):
        if isinstance(item, dict) and item.get('role') == 'teacher':
            return item
    return {
        'phase': 'Introduction',
        'message': 'Class session initialized.',
        'question': 'What do you already know about this topic?',
        'feedback': 'Ready to begin.',
    }


def _heuristic_correct(student_response: str, confidence: int | None) -> bool:
    text = student_response.lower().strip()
    if any(token in text for token in ['idk', "don't know", 'not sure', '?']):
        return False
    if len(text) < 15:
        return False
    if confidence is not None and confidence < 30:
        return False
    return True


def _record_signal(
    *,
    db: Session,
    user_id: int,
    action: str,
    topic: str | None,
    difficulty: str | None,
    confidence: int | None = None,
    was_correct: bool | None = None,
    dwell_seconds: int = 0,
    metadata: dict | None = None,
) -> None:
    db.add(
        SessionSignal(
            user_id=user_id,
            page='classroom',
            event_type='interaction',
            action=action,
            topic=topic,
            task_difficulty=difficulty,
            self_confidence=float(confidence) if confidence is not None else None,
            was_correct=was_correct,
            dwell_seconds=dwell_seconds,
            metadata_json=metadata or {},
        )
    )

def _compress_old_history(user_id: int, db: Session) -> None:
    rows = (
        db.query(ClassroomSession)
        .filter(ClassroomSession.user_id == user_id)
        .order_by(ClassroomSession.started_at.desc(), ClassroomSession.id.desc())
        .all()
    )
    changed = False
    for idx, session in enumerate(rows):
        if idx < 10:
            continue
        transcript = session.transcript_json or []
        if _is_compacted(transcript):
            continue
        summary = session.report_json.get('class_summary') if isinstance(session.report_json, dict) else None
        if not summary:
            teacher_turn = _last_teacher_turn(transcript)
            summary = str(teacher_turn.get('message') or 'Session summary unavailable.')
        session.transcript_json = [
            _compact_marker(),
            {
                'role': 'summary',
                'message': summary[:300],
                'timestamp': _iso(_now()),
            },
        ]
        changed = True
    if changed:
        db.commit()


def _build_state(session: ClassroomSession) -> ClassroomStateResponse:
    lesson_plan = session.lesson_plan_json or []
    transcript = session.transcript_json or []
    phase_idx = int(session.current_phase_index or 0)
    if phase_idx < 0:
        phase_idx = 0
    if lesson_plan and phase_idx >= len(lesson_plan):
        phase_idx = len(lesson_plan) - 1
    current_phase = lesson_plan[phase_idx] if lesson_plan else None

    return ClassroomStateResponse(
        session_id=session.id,
        status=session.status,
        setup={
            'subject': session.subject,
            'topic': session.topic,
            'grade_level': session.grade_level,
            'duration_minutes': session.duration_minutes,
            'difficulty': session.difficulty,
            'learning_goal': session.learning_goal,
            'teacher_style': session.teacher_style,
            'custom_teacher_style': session.custom_teacher_style,
        },
        lesson_plan=lesson_plan,
        current_phase_index=phase_idx,
        current_phase=current_phase,
        adaptive_difficulty=session.adaptive_difficulty,
        teacher_turn=_last_teacher_turn(transcript),
        visuals=session.visuals_json or {},
        transcript=transcript,
        transcript_compacted=_is_compacted(transcript),
        report=session.report_json or {},
    )

@router.post('/start', response_model=ClassroomStateResponse)
def start_classroom(
    payload: ClassroomStartRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = get_ai_provider()
    plan = provider.generate_classroom_plan(payload.model_dump())

    lesson_plan = plan.get('lesson_plan') if isinstance(plan, dict) else []
    teacher_turn = plan.get('teacher_turn') if isinstance(plan, dict) else {}
    visuals = plan.get('visuals') if isinstance(plan, dict) else {}
    adaptive = plan.get('adaptive_difficulty') if isinstance(plan, dict) else None

    if not isinstance(lesson_plan, list) or not lesson_plan:
        raise HTTPException(status_code=500, detail='Classroom plan generation failed')
    if not isinstance(teacher_turn, dict):
        teacher_turn = {}
    if not isinstance(visuals, dict):
        visuals = {}

    started_at = _now()
    transcript = [
        {
            'role': 'teacher',
            'phase': str(teacher_turn.get('phase') or lesson_plan[0].get('name') or 'Introduction'),
            'message': str(teacher_turn.get('message') or 'Welcome to class.'),
            'question': str(teacher_turn.get('question') or ''),
            'feedback': str(teacher_turn.get('feedback') or ''),
            'timestamp': _iso(started_at),
        }
    ]

    session = ClassroomSession(
        user_id=user.id,
        subject=payload.subject,
        topic=payload.topic,
        grade_level=payload.grade_level,
        duration_minutes=payload.duration_minutes,
        difficulty=payload.difficulty,
        learning_goal=payload.learning_goal,
        teacher_style=payload.teacher_style,
        custom_teacher_style=payload.custom_teacher_style,
        status='in_progress',
        current_phase_index=0,
        adaptive_difficulty=str(adaptive or payload.difficulty),
        lesson_plan_json=lesson_plan,
        visuals_json=visuals,
        transcript_json=transcript,
        report_json={},
        started_at=started_at,
    )
    db.add(session)
    db.flush()

    _record_signal(
        db=db,
        user_id=user.id,
        action='classroom-start',
        topic=session.topic,
        difficulty=session.adaptive_difficulty,
        metadata={'session_id': session.id, 'duration': session.duration_minutes},
    )
    db.commit()

    _compress_old_history(user.id, db)
    db.refresh(session)
    return _build_state(session)

@router.post('/{session_id}/respond', response_model=ClassroomStateResponse)
def respond_classroom(
    session_id: int,
    payload: ClassroomRespondRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ClassroomSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail='Classroom session not found')
    if session.status == 'completed':
        raise HTTPException(status_code=409, detail='Class session already completed')

    student_text = payload.student_response.strip()
    if not student_text:
        raise HTTPException(status_code=400, detail='Student response cannot be empty')

    was_correct = _heuristic_correct(student_text, payload.self_confidence)
    turn_payload = {
        'subject': session.subject,
        'topic': session.topic,
        'grade_level': session.grade_level,
        'lesson_plan': session.lesson_plan_json or [],
        'current_phase_index': session.current_phase_index,
        'adaptive_difficulty': session.adaptive_difficulty,
        'student_response': student_text,
        'self_confidence': payload.self_confidence,
        'was_correct': was_correct,
    }

    provider = get_ai_provider()
    next_turn = provider.classroom_next_turn(turn_payload)

    teacher_turn = next_turn.get('teacher_turn') if isinstance(next_turn, dict) else None
    if not isinstance(teacher_turn, dict):
        raise HTTPException(status_code=500, detail='Classroom turn generation failed')

    phase_idx = int(next_turn.get('current_phase_index') or session.current_phase_index or 0)
    lesson_plan = session.lesson_plan_json or []
    if lesson_plan:
        phase_idx = max(0, min(len(lesson_plan) - 1, phase_idx))

    transcript = list(session.transcript_json or [])
    now_iso = _iso(_now())
    transcript.append(
        {
            'role': 'student',
            'message': student_text,
            'self_confidence': payload.self_confidence,
            'was_correct': was_correct,
            'timestamp': now_iso,
        }
    )
    transcript.append(
        {
            'role': 'teacher',
            'phase': str(teacher_turn.get('phase') or (lesson_plan[phase_idx].get('name') if lesson_plan else 'Classroom')),
            'message': str(teacher_turn.get('message') or ''),
            'question': str(teacher_turn.get('question') or ''),
            'feedback': str(teacher_turn.get('feedback') or ''),
            'timestamp': now_iso,
        }
    )

    session.current_phase_index = phase_idx
    session.adaptive_difficulty = str(next_turn.get('adaptive_difficulty') or session.adaptive_difficulty)
    visuals = next_turn.get('visuals')
    if isinstance(visuals, dict):
        session.visuals_json = visuals
    session.transcript_json = transcript
    db.add(session)

    _record_signal(
        db=db,
        user_id=user.id,
        action='classroom-respond',
        topic=session.topic,
        difficulty=session.adaptive_difficulty,
        confidence=payload.self_confidence,
        was_correct=was_correct,
        metadata={'session_id': session.id, 'phase_index': phase_idx},
    )
    db.commit()
    db.refresh(session)
    return _build_state(session)

@router.post('/{session_id}/end', response_model=ClassroomStateResponse)
def end_classroom(
    session_id: int,
    payload: ClassroomEndRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ClassroomSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail='Classroom session not found')

    provider = get_ai_provider()
    report = provider.generate_classroom_report(
        {
            'subject': session.subject,
            'topic': session.topic,
            'grade_level': session.grade_level,
            'difficulty': session.adaptive_difficulty,
            'lesson_plan': session.lesson_plan_json,
            'transcript': session.transcript_json,
            'reason': payload.reason,
        }
    )
    if not isinstance(report, dict):
        report = {}

    session.status = 'completed'
    session.completed_at = _now()
    session.report_json = report
    db.add(session)

    _record_signal(
        db=db,
        user_id=user.id,
        action='classroom-end',
        topic=session.topic,
        difficulty=session.adaptive_difficulty,
        metadata={'session_id': session.id, 'reason': payload.reason},
    )
    db.commit()

    _compress_old_history(user.id, db)
    db.refresh(session)
    return _build_state(session)

@router.get('/history', response_model=ClassroomHistoryResponse)
def classroom_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _compress_old_history(user.id, db)
    sessions = (
        db.query(ClassroomSession)
        .filter(ClassroomSession.user_id == user.id)
        .order_by(ClassroomSession.started_at.desc(), ClassroomSession.id.desc())
        .limit(50)
        .all()
    )

    rows: list[ClassroomSessionSummary] = []
    for s in sessions:
        transcript = s.transcript_json or []
        rows.append(
            ClassroomSessionSummary(
                id=s.id,
                subject=s.subject,
                topic=s.topic,
                grade_level=s.grade_level,
                status=s.status,
                duration_minutes=s.duration_minutes,
                started_at=_iso(s.started_at),
                completed_at=_iso(s.completed_at),
                transcript_compacted=_is_compacted(transcript),
            )
        )
    return ClassroomHistoryResponse(sessions=rows)


@router.get('/{session_id}', response_model=ClassroomStateResponse)
def classroom_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.get(ClassroomSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail='Classroom session not found')
    return _build_state(session)
