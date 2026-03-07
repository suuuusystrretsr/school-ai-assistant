from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ExamSimulation(Base, TimestampMixin):
    __tablename__ = 'exam_simulations'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    subject: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(16))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    predicted_score: Mapped[int] = mapped_column(Integer, default=0)
    actual_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weak_areas: Mapped[list[str]] = mapped_column(JSON, default=list)


class ExamQuestion(Base, TimestampMixin):
    __tablename__ = 'exam_questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey('exam_simulations.id', ondelete='CASCADE'), index=True)
    prompt: Mapped[str] = mapped_column(String(500))
    choices: Mapped[list[str]] = mapped_column(JSON, default=list)
    correct_answer: Mapped[str] = mapped_column(String(255))
    explanation: Mapped[str] = mapped_column(String(1000))
