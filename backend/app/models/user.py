from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile = relationship('UserProfile', back_populates='user', uselist=False)
    buddy_state = relationship('StudyBuddyState', back_populates='user', uselist=False)


class UserProfile(Base, TimestampMixin):
    __tablename__ = 'user_profiles'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    grade_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_learning_style: Mapped[str] = mapped_column(String(64), default='explanation-first')
    weak_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    study_minutes_per_day: Mapped[int] = mapped_column(Integer, default=90)
    focus_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship('User', back_populates='profile')


class StudyBuddyState(Base, TimestampMixin):
    __tablename__ = 'study_buddy_state'
    __table_args__ = (UniqueConstraint('user_id', name='uq_study_buddy_user_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[int] = mapped_column(Integer, default=50)
    last_check_in: Mapped[date | None] = mapped_column(Date, nullable=True)
    mood: Mapped[str] = mapped_column(String(32), default='focused')
    nudges: Mapped[list[dict]] = mapped_column(JSON, default=list)

    user = relationship('User', back_populates='buddy_state')
