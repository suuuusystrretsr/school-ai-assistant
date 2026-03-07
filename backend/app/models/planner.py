from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PlannerTask(Base, TimestampMixin):
    __tablename__ = 'planner_tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    subject: Mapped[str] = mapped_column(String(120))
    topic: Mapped[str] = mapped_column(String(160))
    due_date: Mapped[date] = mapped_column(Date)
    minutes: Mapped[int] = mapped_column(Integer, default=45)
    priority: Mapped[str] = mapped_column(String(16), default='medium')
    task_type: Mapped[str] = mapped_column(String(32), default='review')
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    completed: Mapped[bool] = mapped_column(default=False)
