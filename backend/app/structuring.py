import json
import logging
import time
from enum import StrEnum

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_run
from app.llm import LLMClient, LLMError, LLMTimeoutError
from app.markers import INJECTION_MARKERS, VAGUE_MARKERS, contains, has_mixed_intents
from app.schemas import StructuredItem

logger = logging.getLogger("foxfocus")
MAX_TEXT_LENGTH = 4000
FALLBACK_TITLE_LENGTH = 120


class ReviewCode(StrEnum):
    """Коды причин из ТЗ: пишутся в audit_runs.error, в ответ API не попадают."""

    EMPTY_INPUT = "EMPTY_INPUT"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    VAGUE_INPUT = "VAGUE_INPUT"
    MIXED_INTENTS = "MIXED_INTENTS"


class TextTooLongError(Exception):
    def __init__(self, length: int):
        super().__init__(f"текст длиннее {MAX_TEXT_LENGTH} символов: {length}")


PARSE_FAILURES = (
    ReviewCode.INVALID_JSON,
    ReviewCode.SCHEMA_MISMATCH,
    ReviewCode.LLM_TIMEOUT,
    ReviewCode.LLM_ERROR,
)


async def structure_text(
    text: str,
    *,
    llm: LLMClient,
    session: AsyncSession,
    action: str = "structure",
    user_id: int | None = None,
) -> tuple[StructuredItem, ReviewCode | None]:
    """Разбирает текст в схему ТЗ и всегда оставляет след в журнале."""
    started = time.perf_counter()

    if len(text) > MAX_TEXT_LENGTH:
        error = TextTooLongError(len(text))
        await record_run(
            session,
            action=action,
            request_payload={"text": text[:MAX_TEXT_LENGTH]},
            response_payload={"detail": str(error)},
            status="error",
            error=ReviewCode.TEXT_TOO_LONG,
            duration_ms=_elapsed_ms(started),
            user_id=user_id,
        )
        raise error

    item, reason, detail = await _structure(text, llm)
    if reason is not None:
        item = item.model_copy(update={"needs_review": True})

    response_payload = item.model_dump(mode="json")
    if detail:
        response_payload["error_detail"] = detail
        logger.warning("llm %s: %s", reason, detail)
    await record_run(
        session,
        action=action,
        request_payload={"text": text},
        response_payload=response_payload,
        status="error" if reason in PARSE_FAILURES else "ok",
        error=reason.value if reason else None,
        duration_ms=_elapsed_ms(started),
        user_id=user_id,
    )
    return item, reason


async def _structure(
    text: str, llm: LLMClient
) -> tuple[StructuredItem, ReviewCode | None, str | None]:
    if not text.strip():
        return _fallback_item(text), ReviewCode.EMPTY_INPUT, None

    try:
        raw = await llm.structure(text)
    except LLMTimeoutError as exc:
        return _fallback_item(text), ReviewCode.LLM_TIMEOUT, str(exc) or "таймаут"
    except LLMError as exc:
        return _fallback_item(text), ReviewCode.LLM_ERROR, str(exc) or "ошибка модели"

    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return _fallback_item(text), ReviewCode.INVALID_JSON, None

    try:
        item = StructuredItem.model_validate(payload)
    except ValidationError:
        return _fallback_item(text), ReviewCode.SCHEMA_MISMATCH, None

    return item, _review_reason(text, item), None


def _review_reason(text: str, item: StructuredItem) -> ReviewCode | None:
    """Называем первопричину: расплывчатый вход важнее, чем низкая уверенность из-за него."""
    if contains(text, INJECTION_MARKERS):
        return ReviewCode.PROMPT_INJECTION
    if contains(text, VAGUE_MARKERS):
        return ReviewCode.VAGUE_INPUT
    if has_mixed_intents(text):
        return ReviewCode.MIXED_INTENTS
    if item.confidence == "low" or item.needs_review:
        return ReviewCode.LOW_CONFIDENCE
    return None


def _fallback_item(text: str) -> StructuredItem:
    """Черновик, когда разбора не получилось: срок и приоритет не выдумываем."""
    title = " ".join(text.split())[:FALLBACK_TITLE_LENGTH]
    return StructuredItem(
        item_type="note",
        title=title or "Пустой ввод",
        due_date=None,
        priority="medium",
        tags=[],
        confidence="low",
        needs_review=True,
    )


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
