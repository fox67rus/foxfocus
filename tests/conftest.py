import os
import tempfile
from pathlib import Path

# Приложение читает DATABASE_URL при старте, поэтому подменяем до импорта app.
_TESTS_DB_DIR = Path(tempfile.mkdtemp(prefix="foxfocus-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TESTS_DB_DIR / 'app.db').as_posix()}"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import create_app  # noqa: E402


def sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        async with app.router.lifespan_context(app):
            yield ac
