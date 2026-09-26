import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.db import create_db_engine, create_session_factory
from app.llm import get_llm_client
from app.routers import ai, capture, health, panel, review, tasks

logger = logging.getLogger("foxfocus")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_db_engine(settings.database_url, settings.sqlite_busy_timeout_ms)
    app.state.db_engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.llm = get_llm_client(settings)
    logger.info("database: %s", engine.url.render_as_string(hide_password=True))
    logger.info("llm mode: %s", settings.llm_mode)
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(ai.router)
    app.include_router(capture.router)
    app.include_router(tasks.router)
    app.include_router(review.router)
    app.include_router(panel.router)
    return app


app = create_app()
