from pydantic import BaseModel, Field


class ClassroomStartRequest(BaseModel):
    subject: str
    topic: str
    grade_level: str
    duration_minutes: int = Field(default=45, ge=15, le=90)
    difficulty: str = 'standard'
    learning_goal: str | None = None
    teacher_style: str = 'Standard teacher'
    custom_teacher_style: str | None = None


class ClassroomRespondRequest(BaseModel):
    student_response: str
    self_confidence: int | None = Field(default=None, ge=0, le=100)


class ClassroomEndRequest(BaseModel):
    reason: str | None = None


class ClassroomSessionSummary(BaseModel):
    id: int
    subject: str
    topic: str
    grade_level: str
    status: str
    duration_minutes: int
    started_at: str | None = None
    completed_at: str | None = None
    transcript_compacted: bool = False


class ClassroomStateResponse(BaseModel):
    session_id: int
    status: str
    setup: dict
    lesson_plan: list[dict]
    current_phase_index: int
    current_phase: dict | None
    adaptive_difficulty: str
    teacher_turn: dict
    visuals: dict
    transcript: list[dict]
    transcript_compacted: bool = False
    report: dict


class ClassroomHistoryResponse(BaseModel):
    sessions: list[ClassroomSessionSummary]
