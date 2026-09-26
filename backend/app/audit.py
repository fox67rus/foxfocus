import logging
import time
from types import TracebackType
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditRun

logger = logging.getLogger("foxfocus")

NOT_FOUND = "NOT_FOUND"
INTERNAL_ERROR = "INTERNAL_ERROR"


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


class Journal:
    """Точка доступа под журналом: строка появится и при успехе, и при 404, и при 500."""

    def __init__(self, session: AsyncSession, action: str, request_payload: Any | None):
        self.session = session
        self.action = action
        self.request_payload = request_payload
        self.response: Any | None = None
        self.user_id: int | None = None
        self.error: str | None = None
        self._started = time.perf_counter()

    async def __aenter__(self) -> "Journal":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exc is None:
            await self._write(status="ok", error=self.error, response=self.response)
            return False

        # Транзакция запроса уже испорчена, но строка журнала обязана появиться.
        await self.session.rollback()
        if isinstance(exc, HTTPException):
            code = NOT_FOUND if exc.status_code == 404 else f"HTTP_{exc.status_code}"
            await self._write(status="error", error=code, response={"detail": exc.detail})
        else:
            await self._write(status="error", error=INTERNAL_ERROR, response={"detail": str(exc)})
        return False

    async def _write(self, *, status: str, error: str | None, response: Any | None) -> None:
        try:
            await record_run(
                self.session,
                action=self.action,
                request_payload=self.request_payload,
                response_payload=response,
                status=status,
                error=error,
                duration_ms=int((time.perf_counter() - self._started) * 1000),
                user_id=self.user_id,
            )
        except Exception:  # журнал не должен подменять собой исходную ошибку
            logger.exception("не удалось записать audit_runs для %s", self.action)
