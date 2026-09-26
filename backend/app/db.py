from pathlib import Path

from sqlalchemy import MetaData, event, make_url
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# Предсказуемые имена ограничений: без них SQLite не даёт менять таблицы миграциями.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_engine(url: str, busy_timeout_ms: int = 5000) -> AsyncEngine:
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        _ensure_parent_dir(parsed.database)

    engine = create_async_engine(url, echo=False, future=True)
    if engine.dialect.name == "sqlite":
        _register_sqlite_pragmas(engine.sync_engine, busy_timeout_ms)
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


def _ensure_parent_dir(database: str | None) -> None:
    if not database or database == ":memory:":
        return
    Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _register_sqlite_pragmas(sync_engine: Engine, busy_timeout_ms: int) -> None:
    # PRAGMA не принимает bind-параметры, поэтому значение приводим к int.
    busy_timeout = int(busy_timeout_ms)

    @event.listens_for(sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={busy_timeout}")
        finally:
            cursor.close()
