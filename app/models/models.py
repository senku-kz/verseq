from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)


class TypingSession(Base):
    __tablename__ = "typing_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    exercise_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(2))  # "en" | "ru"
    wpm: Mapped[float]
    cpm: Mapped[float]
    accuracy: Mapped[float]
    duration_ms: Mapped[int]
    error_matrix_delta: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[int]
    exercise_id: Mapped[str] = mapped_column(String(100))
    completed: Mapped[bool] = mapped_column(default=False)
    stars: Mapped[int] = mapped_column(default=0)
    best_wpm: Mapped[float] = mapped_column(default=0.0)
    best_accuracy: Mapped[float] = mapped_column(default=0.0)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)


class UserErrorMatrix(Base):
    __tablename__ = "user_error_matrices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    matrix_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow)
