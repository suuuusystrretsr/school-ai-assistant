from pydantic import BaseModel


class ExamGenerateRequest(BaseModel):
    subject: str
    difficulty: str = 'medium'
    duration_minutes: int = 45


class ExamSubmitRequest(BaseModel):
    answers: dict[int, str]


class ExamGenerateResponse(BaseModel):
    exam_id: int
    subject: str
    difficulty: str
    duration_minutes: int
    predicted_score: int
    questions: list[dict]


class ExamResultResponse(BaseModel):
    exam_id: int
    actual_score: int
    weak_areas: list[str]
    next_topics: list[str]
