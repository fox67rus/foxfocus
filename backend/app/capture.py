from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMClient
from app.models import SOURCE_TEXT_MAX_LENGTH, Note, Task, User
from app.schemas import StructuredItem
from app.structuring import ReviewCode, structure_text


async def capture_item(
    text: str,
    *,
    user: User,
    llm: LLMClient,
    session: AsyncSession,
) -> tuple[Task | Note, StructuredItem]:
    """Разбирает текст и сохраняет ровно одну сущность: задачу или заметку."""
    item, reason = await structure_text(text, llm=llm, session=session, user_id=user.id)
    row = _build_row(text, user=user, item=item, reason=reason)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row, item


def _build_row(
    text: str, *, user: User, item: StructuredItem, reason: ReviewCode | None
) -> Task | Note:
    source_text = text[:SOURCE_TEXT_MAX_LENGTH]
    review_reason = reason.value if reason else None

    if item.item_type == "task":
        return Task(
            user_id=user.id,
            title=item.title,
            due_date=item.due_date,
            priority=item.priority,
            status="todo",
            tags_json=item.tags,
            needs_review=item.needs_review,
            review_reason=review_reason,
            source_text=source_text,
        )
    return Note(
        user_id=user.id,
        text=source_text,
        title=item.title,
        tags_json=item.tags,
        needs_review=item.needs_review,
        review_reason=review_reason,
        source_text=source_text,
    )
