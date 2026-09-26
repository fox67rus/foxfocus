from datetime import UTC, datetime

from sqlalchemy import select

from app.models import Task
from tests.test_capture import runs_for

TASK_TEXT = "отправить договор клиенту"
OTHER_TASK_TEXT = "оплатить хостинг"


async def capture(client, text: str, user_id: str = "u_1") -> dict:
    response = await client.post("/capture", json={"text": text, "user_id": user_id})
    assert response.status_code == 200
    return response.json()


async def test_tasks_list_returns_own_tasks_with_review_flag(client):
    await capture(client, TASK_TEXT)

    response = await client.get("/tasks", params={"user_id": "u_1"})

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"]
    assert tasks[0]["needs_review"] is False
    assert tasks[0]["status"] == "todo"


async def test_timestamps_are_returned_in_utc(client):
    await capture(client, TASK_TEXT)

    created_at = (await client.get("/tasks", params={"user_id": "u_1"})).json()[0]["created_at"]

    assert datetime.fromisoformat(created_at).tzinfo == UTC


async def test_tasks_of_other_user_are_invisible(client):
    await capture(client, TASK_TEXT, user_id="u_1")

    assert (await client.get("/tasks", params={"user_id": "u_2"})).json() == []


async def task_ids(client, **params) -> list[int]:
    response = await client.get("/tasks", params={"user_id": "u_1", **params})
    assert response.status_code == 200
    return [task["id"] for task in response.json()]


async def test_open_and_done_filters(client):
    open_task = await capture(client, TASK_TEXT)
    done_task = await capture(client, OTHER_TASK_TEXT)
    await client.post(f"/tasks/{done_task['item_id']}/done", json={"user_id": "u_1"})

    open_ids = await task_ids(client, status="open")
    done_ids = await task_ids(client, status="done")
    all_ids = await task_ids(client)

    assert open_ids == [open_task["item_id"]]
    assert done_ids == [done_task["item_id"]]
    assert sorted(all_ids) == sorted([open_task["item_id"], done_task["item_id"]])


async def test_done_is_idempotent(client, db_sessions):
    task = await capture(client, TASK_TEXT)

    first = await client.post(f"/tasks/{task['item_id']}/done", json={"user_id": "u_1"})
    second = await client.post(f"/tasks/{task['item_id']}/done", json={"user_id": "u_1"})

    assert first.status_code == 200
    assert first.json() == {"status": "ok"}
    assert second.status_code == 200
    assert second.json() == {"status": "ok"}
    async with db_sessions() as session:
        assert (await session.scalars(select(Task))).one().status == "done"


async def test_done_on_foreign_task_is_404_and_changes_nothing(client, db_sessions):
    task = await capture(client, TASK_TEXT, user_id="u_1")

    response = await client.post(f"/tasks/{task['item_id']}/done", json={"user_id": "u_2"})

    assert response.status_code == 404
    async with db_sessions() as session:
        assert (await session.scalars(select(Task))).one().status == "todo"


async def test_done_on_missing_task_is_404_and_audited(client, db_sessions):
    response = await client.post("/tasks/9999/done", json={"user_id": "u_1"})

    assert response.status_code == 404
    runs = await runs_for(db_sessions, "done")
    assert len(runs) == 1
    assert runs[0].status == "error"
    assert runs[0].error == "NOT_FOUND"


async def test_unknown_status_filter_is_rejected(client):
    assert (
        await client.get("/tasks", params={"user_id": "u_1", "status": "archived"})
    ).status_code == 422


async def test_tasks_list_and_done_are_audited(client, db_sessions):
    task = await capture(client, TASK_TEXT)
    await client.get("/tasks", params={"user_id": "u_1"})
    await client.post(f"/tasks/{task['item_id']}/done", json={"user_id": "u_1"})

    assert len(await runs_for(db_sessions, "tasks")) == 1
    done_runs = await runs_for(db_sessions, "done")
    assert len(done_runs) == 1
    assert done_runs[0].status == "ok"
    assert done_runs[0].output == {"status": "ok"}
