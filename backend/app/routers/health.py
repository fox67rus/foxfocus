from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import Journal
from app.deps import get_llm, get_session
from app.llm import LLMClient, ping_llm
from app.repository import require_user
from app.schemas import LlmStatusResponse

router = APIRouter(tags=["service"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/llm/status", response_model=LlmStatusResponse)
async def llm_status(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    llm: Annotated[LLMClient, Depends(get_llm)],
    user_id: Annotated[str, Query()],
) -> LlmStatusResponse:
    """Проверка связи с провайдером: GET /models, без генерации."""
    async with Journal(session, "llm_status", {"user_id": user_id}) as journal:
        user = await require_user(session, user_id)
        journal.user_id = user.id
        payload = await ping_llm(llm, request.app.state.settings)
        body = LlmStatusResponse.model_validate(payload)
        journal.response = body.model_dump()
        if body.status == "error":
            journal.error = "LLM_UNREACHABLE"
        return body
