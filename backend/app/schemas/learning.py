from datetime import datetime

from pydantic import BaseModel


class LectureSummarizeRequest(BaseModel):
    content: str
    source_type: str = 'text'


class LectureSummarizeResponse(BaseModel):
    summary: str
    key_concepts: list[str]
    flashcards: list[dict]
    practice_questions: list[dict]
    revision_notes: list[str]


class ExplainMistakeRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str


class ExplainMistakeResponse(BaseModel):
    why_wrong: str
    logic_break: str
    correct_thinking: str
    avoid_next_time: list[str]


class MemoryQueueItem(BaseModel):
    topic: str
    memory_strength: float
    next_review_at: datetime
    urgency: str


class LearningStyleResponse(BaseModel):
    style: str
    confidence: float
    evidence: list[str]


class GapScanResponse(BaseModel):
    missing_prerequisites: list[str]
    foundational_review: list[str]
    prerequisite_practice: list[dict]


class MistakePatternResponse(BaseModel):
    patterns: list[str]
    correction_drills: list[dict]
    focused_practice: list[dict]
