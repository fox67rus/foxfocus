import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError

from app.db import Base, create_db_engine, create_session_factory
from app.models import AuditRun, MemoryFact, Note, Task, User
from tests.conftest import sqlite_url

# Имена из ТЗ. Свои колонки добавлять можно, переименовывать эти — нельзя.
CONTRACT_COLUMNS: dict[str, set[str]] = {
    "users": {"id", "public_id", "created_at"},
    "tasks": {
        "id",
        "created_at",
        "user_id",
        "title",
        "due_date",
        "priority",
        "status",
        "tags_json",
        "needs_review",
    },
    "notes": {"id", "created_at", "user_id", "text", "tags_json", "needs_review"},
    "memory_facts": {"id", "created_at", "user_id", "key", "value"},
    "audit_runs": {
        "id",
        "created_at",
        "action",
        "input",
        "output",
        "status",
        "error",
        "duration_ms",
    },
}


def _columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(db_path) as raw:
        return {row[1] for row in raw.execute(f"PRAGMA table_info({table})")}


@pytest.mark.parametrize("table", sorted(CONTRACT_COLUMNS))
def test_table_columns_match_contract(migrated_db: Path, table: str):
    actual = _columns(migrated_db, table)

    assert actual, f"таблица {table} не создана миграциями"
    missing = CONTRACT_COLUMNS[table] - actual
    assert not missing, f"в таблице {table} потеряны колонки: {sorted(missing)}"


def test_models_and_migrations_do_not_drift(migrated_db: Path):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    engine = create_engine(f"sqlite:///{migrated_db.as_posix()}")
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection, opts={"compare_type": True})
            diff = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert diff == [], f"модели разошлись с миграциями: {diff}"


async def test_demo_users_are_seeded(migrated_db: Path):
    engine = create_db_engine(sqlite_url(migrated_db))
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            public_ids = (await session.scalars(select(User.public_id))).all()
    finally:
        await engine.dispose()

    assert set(public_ids) == {"u_1", "u_2"}


async def test_foreign_key_to_user_is_enforced(migrated_db: Path):
    engine = create_db_engine(sqlite_url(migrated_db))
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            session.add(Task(user_id=9999, title="задача без владельца"))
            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()


async def test_row_defaults_follow_contract(migrated_db: Path):
    engine = create_db_engine(sqlite_url(migrated_db))
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            user = (await session.scalars(select(User).where(User.public_id == "u_1"))).one()
            task = Task(user_id=user.id, title="купить кофе и бумагу")
            note = Note(user_id=user.id, text="идея: вынести разбор в отдельный экран")
            fact = MemoryFact(user_id=user.id, key="часовой пояс", value="UTC+3")
            run = AuditRun(action="capture", status="ok", duration_ms=12)
            session.add_all([task, note, fact, run])
            await session.commit()

            assert task.priority == "medium"
            assert task.status == "todo"
            assert task.due_date is None
            assert task.needs_review is False
            assert task.tags_json == []
            assert task.created_at is not None
            assert note.needs_review is False
            assert note.tags_json == []
            assert run.error is None
            assert fact.created_at is not None
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    ("field", "value"),
    [("priority", "urgent"), ("status", "archived")],
)
async def test_task_rejects_values_outside_contract_enums(
    migrated_db: Path, field: str, value: str
):
    engine = create_db_engine(sqlite_url(migrated_db))
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            user = (await session.scalars(select(User).where(User.public_id == "u_1"))).one()
            session.add(Task(user_id=user.id, title="проверка ограничений", **{field: value}))
            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()
