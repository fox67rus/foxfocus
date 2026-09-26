import os
import tempfile
from pathlib import Path

# Приложение читает DATABASE_URL и LLM_MODE при старте — тесты всегда на моке, без сети.
_TESTS_DB_DIR = Path(tempfile.mkdtemp(prefix="foxfocus-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TESTS_DB_DIR / 'app.db').as_posix()}"
os.environ["LLM_MODE"] = "mock"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.db import create_db_engine, create_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.paths import BACKEND_DIR  # noqa: E402


def sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture
def migrated_db(tmp_path: Path) -> Path:
    """Файл базы, на который накачены все миграции."""
    db_path = tmp_path / "migrated.db"
    command.upgrade(alembic_config(sqlite_url(db_path)), "head")
    return db_path


@pytest.fixture
async def db_sessions(migrated_db: Path):
    """Отдельное подключение к той же базе — чтобы проверять, что записало приложение."""
    engine = create_db_engine(sqlite_url(migrated_db))
    try:
        yield create_session_factory(engine)
    finally:
        await engine.dispose()


@pytest.fixture
def app(migrated_db: Path) -> FastAPI:
    return create_app(Settings(database_url=sqlite_url(migrated_db)))


@pytest.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        async with app.router.lifespan_context(app):
            yield ac
