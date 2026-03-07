from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FlashcardDeck(Base, TimestampMixin):
    __tablename__ = 'flashcard_decks'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_text: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(64), default='notes')


class Flashcard(Base, TimestampMixin):
    __tablename__ = 'flashcards'

    id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey('flashcard_decks.id', ondelete='CASCADE'), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    topic_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty_tag: Mapped[str] = mapped_column(String(16), default='medium')
    spaced_repetition_ready: Mapped[bool] = mapped_column(default=True)
