from datetime import date

from pydantic import BaseModel, EmailStr


class UserProfileUpdate(BaseModel):
    grade_level: str | None = None
    preferred_learning_style: str | None = None
    weak_topics: list[str] | None = None
    target_exam_date: date | None = None
    study_minutes_per_day: int | None = None
    focus_mode_enabled: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    grade_level: str | None
    preferred_learning_style: str
    weak_topics: list[str]
    target_exam_date: date | None
    study_minutes_per_day: int
    focus_mode_enabled: bool

    class Config:
        from_attributes = True
