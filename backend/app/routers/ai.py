from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_llm, get_session
from app.llm import LLMClient
from app.schemas import StructuredItem, StructureRequest
from app.structuring import TextTooLongError, structure_text

router = APIRouter(tags=["ai"])


@router.post("/ai/structure", response_model=StructuredItem)
async def structure(
    payload: StructureRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMClient, Depends(get_llm)],
) -> StructuredItem:
    try:
        item, _ = await structure_text(payload.text, llm=llm, session=session)
    except TextTooLongError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return item
