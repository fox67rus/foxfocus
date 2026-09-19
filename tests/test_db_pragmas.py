from pathlib import Path

from sqlalchemy import text

from app.db import create_db_engine
from tests.conftest import sqlite_url


async def test_sqlite_pragmas_are_enabled_on_every_connection(tmp_path: Path):
    engine = create_db_engine(sqlite_url(tmp_path / "pragma.db"), busy_timeout_ms=7000)

    try:
        for _ in range(2):
            async with engine.connect() as conn:
                journal_mode = (await conn.execute(text("PRAGMA journal_mode"))).scalar_one()
                foreign_keys = (await conn.execute(text("PRAGMA foreign_keys"))).scalar_one()
                busy_timeout = (await conn.execute(text("PRAGMA busy_timeout"))).scalar_one()

            assert journal_mode.lower() == "wal"
            assert foreign_keys == 1
            assert busy_timeout == 7000
    finally:
        await engine.dispose()


async def test_engine_url_comes_from_settings(tmp_path: Path):
    from app.config import Settings

    url = sqlite_url(tmp_path / "from-settings.db")
    settings = Settings(database_url=url)

    assert settings.database_url == url

    engine = create_db_engine(settings.database_url, settings.sqlite_busy_timeout_ms)
    try:
        assert engine.url.database == (tmp_path / "from-settings.db").as_posix()
    finally:
        await engine.dispose()


def test_relative_sqlite_path_is_resolved_against_project_root():
    from app.config import Settings
    from app.paths import PROJECT_DIR

    settings = Settings(database_url="sqlite+aiosqlite:///./data/foxfocus.db")
    expected = (PROJECT_DIR / "data" / "foxfocus.db").as_posix()

    assert settings.database_url == f"sqlite+aiosqlite:///{expected}"
