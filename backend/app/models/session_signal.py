from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SessionSignal(Base, TimestampMixin):
    __tablename__ = 'session_signals'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    page: Mapped[str] = mapped_column(String(120), default='dashboard')
    event_type: Mapped[str] = mapped_column(String(64), default='interaction')
    action: Mapped[str] = mapped_column(String(120), default='view')
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True)
    task_difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    energy_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    self_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    was_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dwell_seconds: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column('metadata', JSON, default=dict)

