from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AnalyticsSnapshot(Base, TimestampMixin):
    __tablename__ = 'analytics_snapshots'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    subject_progress: Mapped[dict] = mapped_column(JSON, default=dict)
    mastery_by_topic: Mapped[dict] = mapped_column(JSON, default=dict)
    recent_performance: Mapped[dict] = mapped_column(JSON, default=dict)
    practice_accuracy: Mapped[int] = mapped_column(Integer, default=0)
    readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    learning_consistency: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    retention_forecast: Mapped[dict] = mapped_column(JSON, default=dict)
    distraction_risk: Mapped[str] = mapped_column(String(16), default='low')
