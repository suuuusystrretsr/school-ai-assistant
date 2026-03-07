from pydantic import BaseModel, Field


class HomeworkSolveRequest(BaseModel):
    question_text: str = Field(min_length=3)
    explanation_mode: str = Field(default='normal')


class HomeworkSolveResponse(BaseModel):
    request_id: int
    solution_id: int
    final_answer: str
    steps: list[str]
    explanation_by_mode: dict[str, str]


class PracticeGenerateRequest(BaseModel):
    source_solution_id: int
    difficulty: str = 'medium'


class PracticeSetResponse(BaseModel):
    id: int
    title: str
    difficulty: str
    questions: list[dict]
    answer_key: list[dict]
    worked_solutions: list[dict]


class WhiteboardPayload(BaseModel):
    strokes: list[dict]
    subject: str = 'math'
