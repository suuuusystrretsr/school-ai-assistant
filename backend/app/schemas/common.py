from datetime import datetime

from pydantic import BaseModel


class APIMessage(BaseModel):
    message: str


class TimestampedModel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
