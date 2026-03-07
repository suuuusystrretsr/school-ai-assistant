from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class StudyRoom(Base, TimestampMixin):
    __tablename__ = 'study_rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_participants: Mapped[int] = mapped_column(Integer, default=5)
    shared_notes: Mapped[str] = mapped_column(Text, default='')
    task_board: Mapped[list[dict]] = mapped_column(JSON, default=list)


class RoomMembership(Base, TimestampMixin):
    __tablename__ = 'room_memberships'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('study_rooms.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(32), default='participant')
    is_present: Mapped[bool] = mapped_column(Boolean, default=False)


class RoomMessage(Base, TimestampMixin):
    __tablename__ = 'room_messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('study_rooms.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(32), default='chat')


class RoomInvite(Base, TimestampMixin):
    __tablename__ = 'room_invites'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('study_rooms.id', ondelete='CASCADE'), index=True)
    invited_by_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    invited_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    status: Mapped[str] = mapped_column(String(16), default='pending')
    invite_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
