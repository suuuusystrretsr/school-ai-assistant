from datetime import date

from pydantic import BaseModel


class ExamDate(BaseModel):
    subject: str
    exam_date: date


class PlannerGenerateRequest(BaseModel):
    exams: list[ExamDate]
    weekly_availability_minutes: int
    weak_topics: list[str]
    priorities: dict[str, int]


class PlannerTaskResponse(BaseModel):
    id: int
    subject: str
    topic: str
    due_date: date
    minutes: int
    priority: str
    task_type: str
    recommendations: list[str]

    class Config:
        from_attributes = True
