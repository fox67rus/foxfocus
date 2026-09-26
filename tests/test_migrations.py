import sqlite3
from pathlib import Path

from alembic import command

from tests.conftest import alembic_config, sqlite_url


def test_migrations_apply_to_fresh_db_file(tmp_path: Path):
    db_path = tmp_path / "migrated.db"
    config = alembic_config(sqlite_url(db_path))

    command.upgrade(config, "head")

    assert db_path.exists()
    with sqlite3.connect(db_path) as raw:
        versions = raw.execute("SELECT version_num FROM alembic_version").fetchall()
        journal_mode = raw.execute("PRAGMA journal_mode").fetchone()[0]

    assert len(versions) == 1
    assert journal_mode.lower() == "wal"


def test_migrations_downgrade_to_base(tmp_path: Path):
    config = alembic_config(sqlite_url(tmp_path / "roundtrip.db"))

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    with sqlite3.connect(tmp_path / "roundtrip.db") as raw:
        versions = raw.execute("SELECT version_num FROM alembic_version").fetchall()
        tables = {
            row[0] for row in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

    assert versions == []
    assert tables == {"alembic_version"}
