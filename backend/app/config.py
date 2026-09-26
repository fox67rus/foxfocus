from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import make_url

from app.paths import DATA_DIR, PROJECT_DIR


def _default_database_url() -> str:
    return f"sqlite+aiosqlite:///{(DATA_DIR / 'foxfocus.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Foxfocus"
    database_url: str = Field(default_factory=_default_database_url)
    sqlite_busy_timeout_ms: int = 5000
    # mock — детерминированные правила без сети. live — ProxyAPI или официальный OpenAI.
    llm_mode: str = "mock"
    proxyapi_key: str = ""
    openai_api_key: str = ""
    openai_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-5.4-mini"
    llm_timeout_seconds: float = 25
    llm_temperature: float = Field(default=0.1, ge=0, le=0.2)

    @field_validator("database_url")
    @classmethod
    def _absolutize_sqlite_path(cls, value: str) -> str:
        """Относительный путь к файлу SQLite считаем от корня проекта, а не от текущего каталога."""
        url = make_url(value)
        if url.get_backend_name() != "sqlite":
            return value
        if not url.database or url.database == ":memory:":
            return value
        path = Path(url.database)
        if path.is_absolute():
            return value
        absolute = (PROJECT_DIR / path).resolve().as_posix()
        # Собираем строку руками: render_as_string экранирует двоеточие диска в C%3A.
        return f"{url.drivername}:///{absolute}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
