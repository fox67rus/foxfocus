from tests.test_capture import runs_for
from tests.test_tasks import capture

NOTE_TEXT = "идея: считать долю записей с пометкой проверки"


async def test_notes_are_listed_per_user(client):
    await capture(client, NOTE_TEXT, user_id="u_1")

    mine = (await client.get("/notes", params={"user_id": "u_1"})).json()
    foreign = (await client.get("/notes", params={"user_id": "u_2"})).json()

    assert len(mine) == 1
    assert mine[0]["text"] == NOTE_TEXT
    assert mine[0]["needs_review"] is False
    assert foreign == []


async def test_audit_shows_own_runs_only(client):
    await capture(client, NOTE_TEXT, user_id="u_1")

    mine = (await client.get("/audit", params={"user_id": "u_1"})).json()
    foreign = (await client.get("/audit", params={"user_id": "u_2"})).json()

    contract_fields = {
        "id",
        "created_at",
        "action",
        "input",
        "output",
        "status",
        "error",
        "duration_ms",
    }
    assert {"capture", "structure"} <= {run["action"] for run in mine}
    assert contract_fields <= set(mine[0])
    assert foreign == []


async def test_panel_endpoints_reject_unknown_user(client, db_sessions):
    assert (await client.get("/notes", params={"user_id": "u_404"})).status_code == 404
    assert (await client.get("/audit", params={"user_id": "u_404"})).status_code == 404

    assert [run.error for run in await runs_for(db_sessions, "notes")] == ["NOT_FOUND"]
    assert [run.error for run in await runs_for(db_sessions, "audit")] == ["NOT_FOUND"]


async def test_audit_returns_newest_first(client):
    await capture(client, "оплатить хостинг", user_id="u_1")
    await capture(client, NOTE_TEXT, user_id="u_1")

    runs = (await client.get("/audit", params={"user_id": "u_1"})).json()

    assert [run["id"] for run in runs] == sorted((run["id"] for run in runs), reverse=True)
