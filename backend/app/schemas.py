from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.models import (
    AuditRun,
    Confidence,
    ItemType,
    Note,
    Priority,
    RunStatus,
    Task,
    TaskStatus,
    as_utc,
)


class StructureRequest(BaseModel):
    text: str


class StructuredItem(BaseModel):
    """Ответ разбора: ровно семь полей ТЗ, ничего сверх схемы.

    Причина ручной проверки сюда не попадает — её код пишется в audit_runs.error.
    """

    model_config = ConfigDict(extra="forbid")

    item_type: ItemType
    title: str
    due_date: date | None
    priority: Priority
    tags: list[str]
    confidence: Confidence
    needs_review: bool


class CaptureRequest(BaseModel):
    text: str
    user_id: str


class CaptureResponse(BaseModel):
    status: str
    item_id: int
    item_type: ItemType
    needs_review: bool


class DoneRequest(BaseModel):
    user_id: str


class StatusResponse(BaseModel):
    status: str


class TaskOut(BaseModel):
    id: int
    created_at: datetime
    title: str
    due_date: date | None
    priority: Priority
    status: TaskStatus
    tags: list[str]
    needs_review: bool
    review_reason: str | None
    source_text: str | None

    @classmethod
    def from_model(cls, task: Task) -> "TaskOut":
        return cls(
            id=task.id,
            created_at=as_utc(task.created_at),
            title=task.title,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status,
            tags=task.tags_json,
            needs_review=task.needs_review,
            review_reason=task.review_reason,
            source_text=task.source_text,
        )


class NoteOut(BaseModel):
    id: int
    created_at: datetime
    text: str
    title: str | None
    tags: list[str]
    needs_review: bool
    review_reason: str | None
    source_text: str | None

    @classmethod
    def from_model(cls, note: Note) -> "NoteOut":
        return cls(
            id=note.id,
            created_at=as_utc(note.created_at),
            text=note.text,
            title=note.title,
            tags=note.tags_json,
            needs_review=note.needs_review,
            review_reason=note.review_reason,
            source_text=note.source_text,
        )


class AuditRunOut(BaseModel):
    id: int
    created_at: datetime
    action: str
    input: Any | None
    output: Any | None
    status: RunStatus
    error: str | None
    duration_ms: int

    @classmethod
    def from_model(cls, run: AuditRun) -> "AuditRunOut":
        return cls(
            id=run.id,
            created_at=as_utc(run.created_at),
            action=run.action,
            input=run.input,
            output=run.output,
            status=run.status,
            error=run.error,
            duration_ms=run.duration_ms,
        )


# Фильтр ТЗ: open — всё, что не done.
TaskFilter = Literal["open", "done"]
