from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class KnowledgeGraphNode(Base, TimestampMixin):
    __tablename__ = 'knowledge_graph_nodes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    subject: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(32), default='not-learned')
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)


class MemoryReviewSchedule(Base, TimestampMixin):
    __tablename__ = 'memory_review_schedule'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    memory_strength: Mapped[float] = mapped_column(Float, default=0.5)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    urgency: Mapped[str] = mapped_column(String(16), default='medium')
