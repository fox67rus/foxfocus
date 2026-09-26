from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import Journal
from app.deps import get_session
from app.repository import list_audit_runs, list_notes, require_user
from app.schemas import AuditRunOut, NoteOut

router = APIRouter(tags=["panel"])

NOTES_LIMIT = 50
AUDIT_LIMIT = 100


@router.get("/notes", response_model=list[NoteOut])
async def read_notes(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str, Query()],
    limit: Annotated[int, Query(ge=1, le=200)] = NOTES_LIMIT,
) -> list[NoteOut]:
    async with Journal(session, "notes", {"user_id": user_id, "limit": limit}) as journal:
        user = await require_user(session, user_id)
        journal.user_id = user.id

        notes = [NoteOut.from_model(note) for note in await list_notes(session, user.id, limit)]
        journal.response = {"count": len(notes)}
        return notes


@router.get("/audit", response_model=list[AuditRunOut])
async def read_audit(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str, Query()],
    limit: Annotated[int, Query(ge=1, le=500)] = AUDIT_LIMIT,
) -> list[AuditRunOut]:
    async with Journal(session, "audit", {"user_id": user_id, "limit": limit}) as journal:
        user = await require_user(session, user_id)
        journal.user_id = user.id

        rows = await list_audit_runs(session, user.id, limit)
        runs = [AuditRunOut.from_model(run) for run in rows]
        journal.response = {"count": len(runs)}
        return runs
