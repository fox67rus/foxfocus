from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import Journal
from app.capture import capture_item
from app.deps import get_llm, get_session
from app.llm import LLMClient
from app.repository import require_user
from app.schemas import CaptureRequest, CaptureResponse
from app.structuring import TextTooLongError

router = APIRouter(tags=["capture"])


@router.post("/capture", response_model=CaptureResponse)
async def capture(
    payload: CaptureRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMClient, Depends(get_llm)],
) -> CaptureResponse:
    async with Journal(session, "capture", payload.model_dump()) as journal:
        user = await require_user(session, payload.user_id)
        journal.user_id = user.id

        try:
            row, item = await capture_item(payload.text, user=user, llm=llm, session=session)
        except TextTooLongError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        response = CaptureResponse(
            status="ok",
            item_id=row.id,
            item_type=item.item_type,
            needs_review=item.needs_review,
        )
        journal.response = response.model_dump(mode="json")
        return response
