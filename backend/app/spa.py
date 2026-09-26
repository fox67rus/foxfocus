from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_spa(app: FastAPI, static_dir: Path) -> None:
    """Отдаёт собранный SPA с того же порта, что и API. Подключается последним."""
    assets = static_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    async def spa_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/{path:path}")
    async def spa_fallback(path: str) -> FileResponse:
        candidate = (static_dir / path).resolve()
        if candidate.is_file() and candidate.is_relative_to(static_dir):
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")
