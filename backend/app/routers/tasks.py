from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import Journal
from app.deps import get_session
from app.repository import list_tasks, require_task, require_user
from app.schemas import DoneRequest, StatusResponse, TaskFilter, TaskOut

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[TaskOut])
async def read_tasks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str, Query()],
    status: Annotated[TaskFilter | None, Query()] = None,
) -> list[TaskOut]:
    async with Journal(session, "tasks", {"user_id": user_id, "status": status}) as journal:
        user = await require_user(session, user_id)
        journal.user_id = user.id

        tasks = [TaskOut.from_model(task) for task in await list_tasks(session, user.id, status)]
        # В журнал пишем размер выдачи: списком журнал начнёт разрастаться сам от себя.
        journal.response = {"count": len(tasks)}
        return tasks


@router.post("/tasks/{task_id}/done", response_model=StatusResponse)
async def mark_task_done(
    task_id: int,
    payload: DoneRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatusResponse:
    request_payload = {"task_id": task_id, "user_id": payload.user_id}
    async with Journal(session, "done", request_payload) as journal:
        user = await require_user(session, payload.user_id)
        journal.user_id = user.id

        task = await require_task(session, user.id, task_id)
        if task.status != "done":
            task.status = "done"
            await session.commit()

        # Повтор по уже закрытой задаче — тоже ok.
        response = StatusResponse(status="ok")
        journal.response = response.model_dump(mode="json")
        return response


@router.post("/tasks/{task_id}/delete", response_model=StatusResponse)
async def delete_task(
    task_id: int,
    payload: DoneRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatusResponse:
    request_payload = {"task_id": task_id, "user_id": payload.user_id}
    async with Journal(session, "delete", request_payload) as journal:
        user = await require_user(session, payload.user_id)
        journal.user_id = user.id

        task = await require_task(session, user.id, task_id)
        await session.delete(task)
        await session.commit()

        response = StatusResponse(status="ok")
        journal.response = response.model_dump(mode="json")
        return response
