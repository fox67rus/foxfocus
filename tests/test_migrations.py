import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.paths import BACKEND_DIR
from tests.conftest import sqlite_url


def _alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_migrations_apply_to_fresh_db_file(tmp_path: Path):
    db_path = tmp_path / "migrated.db"
    config = _alembic_config(sqlite_url(db_path))

    command.upgrade(config, "head")

    assert db_path.exists()
    with sqlite3.connect(db_path) as raw:
        versions = raw.execute("SELECT version_num FROM alembic_version").fetchall()
        journal_mode = raw.execute("PRAGMA journal_mode").fetchone()[0]

    assert len(versions) == 1
    assert journal_mode.lower() == "wal"


def test_migrations_downgrade_to_base(tmp_path: Path):
    config = _alembic_config(sqlite_url(tmp_path / "roundtrip.db"))

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    with sqlite3.connect(tmp_path / "roundtrip.db") as raw:
        versions = raw.execute("SELECT version_num FROM alembic_version").fetchall()

    assert versions == []
