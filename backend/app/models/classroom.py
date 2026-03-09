from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ClassroomSession(Base, TimestampMixin):
    __tablename__ = 'classroom_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)

    subject: Mapped[str] = mapped_column(String(120))
    topic: Mapped[str] = mapped_column(String(200))
    grade_level: Mapped[str] = mapped_column(String(64))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(32), default='standard')
    learning_goal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    teacher_style: Mapped[str] = mapped_column(String(80), default='Standard teacher')
    custom_teacher_style: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default='in_progress')
    current_phase_index: Mapped[int] = mapped_column(Integer, default=0)
    adaptive_difficulty: Mapped[str] = mapped_column(String(32), default='standard')

    lesson_plan_json: Mapped[list[dict]] = mapped_column('lesson_plan', JSON, default=list)
    visuals_json: Mapped[dict] = mapped_column('visuals', JSON, default=dict)
    transcript_json: Mapped[list[dict]] = mapped_column('transcript', JSON, default=list)
    report_json: Mapped[dict] = mapped_column('report', JSON, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
