from sqlalchemy import select

from app.models import Note, Task
from tests.test_capture import runs_for
from tests.test_review import INJECTION_NOTE, VAGUE_TASK
from tests.test_tasks import capture


async def test_delete_task_removes_row_and_is_audited(client, db_sessions):
    captured = await capture(client, VAGUE_TASK)
    task_id = captured["item_id"]

    response = await client.post(
        f"/tasks/{task_id}/delete",
        json={"user_id": "u_1"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    listed = await client.get("/tasks", params={"user_id": "u_1"})
    assert listed.json() == []

    async with db_sessions() as session:
        assert (await session.scalars(select(Task))).first() is None
    deletes = await runs_for(db_sessions, "delete")
    assert len(deletes) == 1
    assert deletes[0].status == "ok"
    assert deletes[0].output == {"status": "ok"}


async def test_delete_foreign_task_is_404_and_changes_nothing(client, db_sessions):
    captured = await capture(client, VAGUE_TASK, user_id="u_1")

    response = await client.post(
        f"/tasks/{captured['item_id']}/delete",
        json={"user_id": "u_2"},
    )

    assert response.status_code == 404
    async with db_sessions() as session:
        assert (await session.scalars(select(Task))).one().needs_review is True


async def test_delete_missing_task_is_404_and_audited(client, db_sessions):
    response = await client.post("/tasks/9999/delete", json={"user_id": "u_1"})

    assert response.status_code == 404
    runs = await runs_for(db_sessions, "delete")
    assert len(runs) == 1
    assert runs[0].error == "NOT_FOUND"


async def test_delete_note_removes_row(client, db_sessions):
    captured = await capture(client, INJECTION_NOTE)
    assert captured["item_type"] == "note"

    response = await client.post(
        f"/notes/{captured['item_id']}/delete",
        json={"user_id": "u_1"},
    )

    assert response.status_code == 200
    listed = await client.get("/notes", params={"user_id": "u_1"})
    assert listed.json() == []
    async with db_sessions() as session:
        assert (await session.scalars(select(Note))).first() is None


async def test_delete_foreign_note_is_404(client, db_sessions):
    captured = await capture(client, INJECTION_NOTE, user_id="u_1")

    response = await client.post(
        f"/notes/{captured['item_id']}/delete",
        json={"user_id": "u_2"},
    )

    assert response.status_code == 404
    async with db_sessions() as session:
        assert (await session.scalars(select(Note))).one() is not None
