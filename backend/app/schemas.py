from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models import Confidence, ItemType, Priority


class StructureRequest(BaseModel):
    text: str


class StructuredItem(BaseModel):
    """Ответ разбора: ровно семь полей ТЗ, ничего сверх схемы.

    Причина ручной проверки сюда не попадает — её код пишется в audit_runs.error.
    """

    model_config = ConfigDict(extra="forbid")

    item_type: ItemType
    title: str
    due_date: date | None
    priority: Priority
    tags: list[str]
    confidence: Confidence
    needs_review: bool
