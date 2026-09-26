from datetime import UTC, date, datetime
from typing import Any, Literal, get_args

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

ItemType = Literal["task", "note"]
Priority = Literal["low", "medium", "high"]
Confidence = Literal["high", "medium", "low"]
TaskStatus = Literal["todo", "in_progress", "done"]
RunStatus = Literal["ok", "error"]

PRIORITIES: tuple[str, ...] = get_args(Priority)
TASK_STATUSES: tuple[str, ...] = get_args(TaskStatus)
RUN_STATUSES: tuple[str, ...] = get_args(RunStatus)

TITLE_MAX_LENGTH = 500
SOURCE_TEXT_MAX_LENGTH = 4000


def utc_now() -> datetime:
    return datetime.now(UTC)


def _in_values(column: str, values: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({allowed})"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Внешний идентификатор из запросов API: u_1, u_2, позже uuid.
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(_in_values("priority", PRIORITIES), name="priority"),
        CheckConstraint(_in_values("status", TASK_STATUSES), name="status"),
        Index("ix_tasks_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="todo", nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Расширения поверх ТЗ.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_text: Mapped[str | None] = mapped_column(String(SOURCE_TEXT_MAX_LENGTH), nullable=True)

    user: Mapped[User] = relationship()


class Note(TimestampMixin, Base):
    __tablename__ = "notes"
    __table_args__ = (Index("ix_notes_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Расширения поверх ТЗ.
    title: Mapped[str | None] = mapped_column(String(TITLE_MAX_LENGTH), nullable=True)
    review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_text: Mapped[str | None] = mapped_column(String(SOURCE_TEXT_MAX_LENGTH), nullable=True)

    user: Mapped[User] = relationship()


class MemoryFact(TimestampMixin, Base):
    __tablename__ = "memory_facts"
    __table_args__ = (Index("ix_memory_facts_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship()


class AuditRun(TimestampMixin, Base):
    """Строка журнала: её пишет любая точка доступа, включая ошибки и таймауты модели."""

    __tablename__ = "audit_runs"
    __table_args__ = (
        CheckConstraint(_in_values("status", RUN_STATUSES), name="status"),
        Index("ix_audit_runs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    input: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    output: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # Код причины ручной проверки (LOW_CONFIDENCE, INVALID_JSON, ...) или текст ошибки.
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Расширение поверх ТЗ: журнал тоже показывается в разрезе пользователя.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped[User | None] = relationship()


__all__ = [
    "PRIORITIES",
    "RUN_STATUSES",
    "SOURCE_TEXT_MAX_LENGTH",
    "TASK_STATUSES",
    "TITLE_MAX_LENGTH",
    "AuditRun",
    "Confidence",
    "ItemType",
    "MemoryFact",
    "Note",
    "Priority",
    "RunStatus",
    "Task",
    "TaskStatus",
    "User",
    "utc_now",
]
