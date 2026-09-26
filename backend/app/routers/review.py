from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import Journal
from app.deps import get_session
from app.repository import require_note, require_task, require_user
from app.schemas import NoteOut, NoteReviewRequest, TaskOut, TaskReviewRequest

router = APIRouter(tags=["review"])


@router.post("/tasks/{task_id}/review", response_model=TaskOut)
async def review_task(
    task_id: int,
    payload: TaskReviewRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskOut:
    request_payload = payload.model_dump(mode="json") | {"task_id": task_id}
    async with Journal(session, "update", request_payload) as journal:
        user = await require_user(session, payload.user_id)
        journal.user_id = user.id

        task = await require_task(session, user.id, task_id)
        task.title = payload.title
        task.priority = payload.priority
        if "due_date" in payload.model_fields_set:
            task.due_date = payload.due_date
        task.needs_review = False
        task.review_reason = None
        await session.commit()
        await session.refresh(task)

        response = TaskOut.from_model(task)
        journal.response = response.model_dump(mode="json")
        return response


@router.post("/notes/{note_id}/review", response_model=NoteOut)
async def review_note(
    note_id: int,
    payload: NoteReviewRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteOut:
    request_payload = payload.model_dump() | {"note_id": note_id}
    async with Journal(session, "update", request_payload) as journal:
        user = await require_user(session, payload.user_id)
        journal.user_id = user.id

        note = await require_note(session, user.id, note_id)
        note.title = payload.title
        note.needs_review = False
        note.review_reason = None
        await session.commit()
        await session.refresh(note)

        response = NoteOut.from_model(note)
        journal.response = response.model_dump(mode="json")
        return response
