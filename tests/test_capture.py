from sqlalchemy import select

from app.models import AuditRun, Note, Task, User
from app.structuring import MAX_TEXT_LENGTH, ReviewCode

CAPTURE_FIELDS = {"status", "item_id", "item_type", "needs_review"}


async def runs_for(db_sessions, action: str) -> list[AuditRun]:
    async with db_sessions() as session:
        query = select(AuditRun).where(AuditRun.action == action).order_by(AuditRun.id)
        return list((await session.scalars(query)).all())


async def test_capture_creates_task(client, db_sessions):
    response = await client.post(
        "/capture", json={"text": "отправить счёт клиенту Иванову", "user_id": "u_1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == CAPTURE_FIELDS
    assert body["status"] == "ok"
    assert body["item_type"] == "task"
    assert body["needs_review"] is False

    async with db_sessions() as session:
        task = (await session.scalars(select(Task))).one()
        user = (await session.scalars(select(User).where(User.public_id == "u_1"))).one()
    assert task.id == body["item_id"]
    assert task.user_id == user.id
    assert task.status == "todo"
    assert task.source_text == "отправить счёт клиенту Иванову"


async def test_capture_creates_note(client, db_sessions):
    text = "идея: показывать причину проверки прямо в списке"

    body = (await client.post("/capture", json={"text": text, "user_id": "u_1"})).json()

    assert body["item_type"] == "note"
    async with db_sessions() as session:
        note = (await session.scalars(select(Note))).one()
    assert note.id == body["item_id"]
    assert note.text == text


async def test_capture_keeps_review_reason_on_item(client, db_sessions):
    body = (await client.post("/capture", json={"text": "сделай важное", "user_id": "u_1"})).json()

    assert body["needs_review"] is True
    async with db_sessions() as session:
        item = (await session.scalars(select(Task))).one()
    assert item.id == body["item_id"]
    assert item.needs_review is True
    assert item.review_reason == ReviewCode.VAGUE_INPUT
    assert item.due_date is None


async def test_capture_writes_audit_with_user(client, db_sessions):
    await client.post("/capture", json={"text": "оплатить хостинг", "user_id": "u_1"})

    captures = await runs_for(db_sessions, "capture")
    structures = await runs_for(db_sessions, "structure")
    assert len(captures) == 1
    assert len(structures) == 1, "разбор модели тоже должен быть виден в журнале"
    assert captures[0].status == "ok"
    assert captures[0].input == {"text": "оплатить хостинг", "user_id": "u_1"}
    assert captures[0].output["item_type"] == "task"
    assert captures[0].user_id is not None
    assert structures[0].user_id == captures[0].user_id


async def test_capture_for_unknown_user_is_404_and_audited(client, db_sessions):
    response = await client.post("/capture", json={"text": "купить кофе", "user_id": "u_404"})

    assert response.status_code == 404
    captures = await runs_for(db_sessions, "capture")
    assert len(captures) == 1
    assert captures[0].status == "error"
    assert captures[0].error == "NOT_FOUND"

    async with db_sessions() as session:
        assert (await session.scalars(select(Task))).all() == []


async def test_capture_rejects_too_long_text(client, db_sessions):
    response = await client.post(
        "/capture", json={"text": "а" * (MAX_TEXT_LENGTH + 1), "user_id": "u_1"}
    )

    assert response.status_code == 422
    assert await runs_for(db_sessions, "capture")
