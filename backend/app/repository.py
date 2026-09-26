from collections.abc import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditRun, Note, Task, User
from app.schemas import TaskFilter

# Чужой или несуществующий ресурс отвечает одинаково: наружу не видно, что он вообще есть.
NOT_FOUND_DETAIL = "не найдено"


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


async def require_user(session: AsyncSession, public_id: str) -> User:
    user = (await session.scalars(select(User).where(User.public_id == public_id))).first()
    if user is None:
        raise not_found()
    return user


async def list_tasks(
    session: AsyncSession, user_id: int, status: TaskFilter | None = None
) -> Sequence[Task]:
    query = select(Task).where(Task.user_id == user_id)
    if status == "open":
        # По ТЗ open — всё, что не done.
        query = query.where(Task.status != "done")
    elif status == "done":
        query = query.where(Task.status == "done")
    return (await session.scalars(query.order_by(Task.id.desc()))).all()


async def require_task(session: AsyncSession, user_id: int, task_id: int) -> Task:
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = (await session.scalars(query)).first()
    if task is None:
        raise not_found()
    return task


async def require_note(session: AsyncSession, user_id: int, note_id: int) -> Note:
    query = select(Note).where(Note.id == note_id, Note.user_id == user_id)
    note = (await session.scalars(query)).first()
    if note is None:
        raise not_found()
    return note


async def list_notes(session: AsyncSession, user_id: int, limit: int) -> Sequence[Note]:
    query = select(Note).where(Note.user_id == user_id).order_by(Note.id.desc()).limit(limit)
    return (await session.scalars(query)).all()


async def list_audit_runs(session: AsyncSession, user_id: int, limit: int) -> Sequence[AuditRun]:
    query = (
        select(AuditRun)
        .where(AuditRun.user_id == user_id)
        .order_by(AuditRun.id.desc())
        .limit(limit)
    )
    return (await session.scalars(query)).all()
