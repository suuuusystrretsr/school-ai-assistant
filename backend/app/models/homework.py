from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class HomeworkRequest(Base, TimestampMixin):
    __tablename__ = 'homework_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), default='text')
    attachment_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation_mode: Mapped[str] = mapped_column(String(32), default='normal')


class GeneratedSolution(Base, TimestampMixin):
    __tablename__ = 'generated_solutions'

    id: Mapped[int] = mapped_column(primary_key=True)
    homework_request_id: Mapped[int] = mapped_column(
        ForeignKey('homework_requests.id', ondelete='CASCADE'), index=True
    )
    final_answer: Mapped[str] = mapped_column(Text)
    steps: Mapped[list[str]] = mapped_column(JSON, default=list)
    simplified_explanation: Mapped[str] = mapped_column(Text)
    advanced_explanation: Mapped[str] = mapped_column(Text)
    teacher_mode_explanation: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[int] = mapped_column(Integer, default=75)


class PracticeSet(Base, TimestampMixin):
    __tablename__ = 'practice_sets'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    source_solution_id: Mapped[int | None] = mapped_column(
        ForeignKey('generated_solutions.id', ondelete='SET NULL'), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(16), default='medium')
    questions: Mapped[list[dict]] = mapped_column(JSON, default=list)
    answer_key: Mapped[list[dict]] = mapped_column(JSON, default=list)
    worked_solutions: Mapped[list[dict]] = mapped_column(JSON, default=list)
