from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditRun


async def record_run(
    session: AsyncSession,
    *,
    action: str,
    request_payload: Any | None,
    response_payload: Any | None,
    status: str,
    error: str | None,
    duration_ms: int,
    user_id: int | None = None,
) -> AuditRun:
    """Строку журнала пишет любая точка доступа, включая ошибки и таймауты модели."""
    run = AuditRun(
        action=action,
        input=request_payload,
        output=response_payload,
        status=status,
        error=error,
        duration_ms=duration_ms,
        user_id=user_id,
    )
    session.add(run)
    await session.commit()
    return run
