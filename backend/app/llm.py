import json
import re
from datetime import date, timedelta
from typing import Any, Protocol

from app.config import Settings
from app.markers import (
    ACTION_MARKERS,
    HIGH_PRIORITY_MARKERS,
    LOW_PRIORITY_MARKERS,
    NOTE_MARKERS,
    VAGUE_MARKERS,
    contains,
    has_mixed_intents,
)
from app.models import utc_now


class LLMError(Exception):
    """Модель не смогла ответить."""


class LLMTimeoutError(LLMError):
    """Модель не ответила за отведённое время."""


class LLMClient(Protocol):
    async def structure(self, text: str) -> str:
        """Возвращает сырой ответ модели — его ещё предстоит разобрать и проверить."""
        ...


ISO_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
TITLE_MAX_LENGTH = 120


class MockLLM:
    """Детерминированная замена модели: те же правила, но без сети и без ключей.

    Ничего не додумывает: срок появляется только там, где он явно написан в тексте.
    """

    async def structure(self, text: str) -> str:
        return json.dumps(self._draft(text), ensure_ascii=False)

    def _draft(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        item_type = self._item_type(lowered)
        confidence = self._confidence(lowered)
        return {
            "item_type": item_type,
            "title": self._title(text),
            "due_date": self._due_date(lowered),
            "priority": self._priority(lowered),
            "tags": [],
            "confidence": confidence,
            "needs_review": confidence == "low",
        }

    @staticmethod
    def _item_type(lowered: str) -> str:
        if contains(lowered, NOTE_MARKERS):
            return "note"
        if contains(lowered, ACTION_MARKERS):
            return "task"
        return "note"

    @staticmethod
    def _title(text: str) -> str:
        title = " ".join(text.split())
        if len(title) > TITLE_MAX_LENGTH:
            title = title[: TITLE_MAX_LENGTH - 1].rstrip() + "…"
        return title

    @staticmethod
    def _due_date(lowered: str) -> str | None:
        iso = ISO_DATE.search(lowered)
        if iso:
            return iso.group(1)
        today: date = utc_now().date()
        if "послезавтра" in lowered:
            return (today + timedelta(days=2)).isoformat()
        if "завтра" in lowered:
            return (today + timedelta(days=1)).isoformat()
        if "сегодня" in lowered:
            return today.isoformat()
        return None

    @staticmethod
    def _priority(lowered: str) -> str:
        if contains(lowered, HIGH_PRIORITY_MARKERS):
            return "high"
        if contains(lowered, LOW_PRIORITY_MARKERS):
            return "low"
        return "medium"

    @staticmethod
    def _confidence(lowered: str) -> str:
        vague = contains(lowered, VAGUE_MARKERS) or has_mixed_intents(lowered)
        if vague or len(lowered.split()) < 2:
            return "low"
        if contains(lowered, ACTION_MARKERS):
            return "high"
        return "medium"


def get_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_mode == "mock":
        return MockLLM()
    raise ValueError(f"неизвестный LLM_MODE: {settings.llm_mode}")
