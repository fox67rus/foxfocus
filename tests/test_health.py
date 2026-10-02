import json

from sqlalchemy import select

from app.models import AuditRun


async def test_health_returns_ok(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_llm_status_mock_is_ok_and_audited(client, db_sessions):
    response = await client.get("/llm/status", params={"user_id": "u_1"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "mock"
    assert body["detail"] is None
    dumped = json.dumps(body)
    assert "sk-" not in dumped
    assert "api_key" not in dumped

    async with db_sessions() as session:
        query = select(AuditRun).where(AuditRun.action == "llm_status")
        runs = (await session.scalars(query)).all()
    assert len(runs) == 1
    assert runs[0].status == "ok"


async def test_llm_status_unknown_user_is_404(client):
    response = await client.get("/llm/status", params={"user_id": "nobody"})

    assert response.status_code == 404
