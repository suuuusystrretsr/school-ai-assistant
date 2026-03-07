from pydantic import BaseModel, Field


class FlashcardGenerateRequest(BaseModel):
    title: str = Field(min_length=2)
    source_text: str = Field(min_length=20)
    source_type: str = 'notes'


class FlashcardItem(BaseModel):
    question: str
    answer: str
    topic_tags: list[str]
    difficulty_tag: str


class FlashcardDeckResponse(BaseModel):
    deck_id: int
    title: str
    cards: list[FlashcardItem]
