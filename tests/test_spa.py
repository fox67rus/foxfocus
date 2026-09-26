from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from tests.conftest import sqlite_url


async def test_spa_is_served_on_same_port_as_api(tmp_path, migrated_db):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<!doctype html><title>Foxfocus</title>", encoding="utf-8")
    (static / "assets").mkdir()
    (static / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")

    app = create_app(
        Settings(database_url=sqlite_url(migrated_db), static_dir=str(static), llm_mode="mock")
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with app.router.lifespan_context(app):
            index = await client.get("/")
            asset = await client.get("/assets/app.js")
            unknown = await client.get("/tasks-page")
            health = await client.get("/health")

    assert index.status_code == 200
    assert "Foxfocus" in index.text
    assert asset.status_code == 200
    assert "console.log" in asset.text
    assert unknown.status_code == 200
    assert "Foxfocus" in unknown.text
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


async def test_root_stays_404_without_frontend_build(client):
    assert (await client.get("/")).status_code == 404
