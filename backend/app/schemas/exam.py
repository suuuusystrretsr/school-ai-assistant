from pydantic import BaseModel, Field


class ExamGenerateRequest(BaseModel):
    subject: str
    topic: str | None = None
    difficulty: str = 'medium'
    duration_minutes: int = Field(default=45, ge=5, le=180)
    question_count: int = Field(default=5, ge=3, le=25)
    teacher_style: str = 'exam-board style'
    custom_teacher_style: str | None = None


class ExamSubmitRequest(BaseModel):
    answers: dict[int, str]
    confidence_by_question: dict[int, int] | None = None


class ExamGenerateResponse(BaseModel):
    exam_id: int
    subject: str
    topic: str
    difficulty: str
    duration_minutes: int
    question_count: int
    teacher_style: str
    predicted_score: int
    questions: list[dict]


class ExamQuestionReview(BaseModel):
    question_id: int
    prompt: str
    choices: list[str]
    selected_answer: str | None
    correct_answer: str
    is_correct: bool
    explanation: str


class ExamResultResponse(BaseModel):
    exam_id: int
    actual_score: int
    weak_areas: list[str]
    next_topics: list[str]
    reviews: list[ExamQuestionReview]
    confidence_gap: int
    outcome_simulation: dict
