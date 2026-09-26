from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


def resolve_static_dir(explicit: str = "") -> Path | None:
    """Каталог собранной панели: явный путь, затем static/, затем frontend/dist."""
    candidates = []
    if explicit.strip():
        candidates.append(Path(explicit.strip()))
    candidates.append(PROJECT_DIR / "static")
    candidates.append(PROJECT_DIR / "frontend" / "dist")
    for path in candidates:
        if (path / "index.html").is_file():
            return path.resolve()
    return None
