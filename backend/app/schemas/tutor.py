from pydantic import BaseModel


class TutorChatRequest(BaseModel):
    message: str
    subject: str = 'general'
    mode: str = 'normal'


class TutorChatResponse(BaseModel):
    reply: str
    follow_up_question: str
    mini_quiz: list[dict]
    adaptive_path: list[str]
