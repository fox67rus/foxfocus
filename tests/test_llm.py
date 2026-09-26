import os

import httpx
import pytest
from openai import APIConnectionError, APITimeoutError

from app.config import Settings
from app.llm import (
    LLMTimeoutError,
    MockLLM,
    OpenAILLM,
    describe_llm,
    get_llm_client,
    resolve_provider,
)
from app.structuring import ReviewCode
from tests.conftest import sqlite_url
from tests.test_ai_structure import last_run

PROXY_BASE = "https://api.proxyapi.ru/openai/v1"
OPENAI_BASE = "https://api.openai.com/v1"


def _settings(**overrides) -> Settings:
    defaults = {
        "llm_mode": "live",
        "proxyapi_key": "",
        "openai_api_key": "",
        "openai_key": "",
        "openai_base_url": "",
        "openai_model": "gpt-5.4-mini",
        "llm_timeout_seconds": 25,
        "llm_temperature": 0.1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class _FakeCompletions:
    def __init__(self, error: Exception | None = None, content: str = "{}"):
        self.error = error
        self.content = content
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        message = type("Message", (), {"content": self.content})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


class _FakeClient:
    def __init__(self, completions: _FakeCompletions):
        self.chat = type("Chat", (), {"completions": completions})()


def test_pytest_default_client_is_mock():
    assert isinstance(get_llm_client(Settings(llm_mode="mock")), MockLLM)


def test_mock_path_does_not_construct_openai_client(monkeypatch):
    def fail_init(self, *args, **kwargs):
        raise AssertionError("мок не должен создавать клиент OpenAI")

    monkeypatch.setattr("openai.AsyncOpenAI.__init__", fail_init)

    client = get_llm_client(Settings(llm_mode="mock"))
    assert isinstance(client, MockLLM)


def test_proxyapi_key_wins_over_openai():
    provider = resolve_provider(
        _settings(proxyapi_key="sk-proxy-real", openai_api_key="sk-openai-real")
    )

    assert provider.name == "proxyapi"
    assert provider.base_url == PROXY_BASE
    assert provider.api_key == "sk-proxy-real"


def test_placeholder_proxy_key_is_ignored():
    provider = resolve_provider(
        _settings(proxyapi_key="YOUR_API_KEY", openai_api_key="sk-openai-real")
    )

    assert provider.name == "openai"
    assert provider.base_url == OPENAI_BASE


def test_openai_key_alias_from_environment():
    provider = resolve_provider(_settings(openai_key="sk-os-real"))

    assert provider.name == "openai"
    assert provider.api_key == "sk-os-real"


def test_custom_base_url_overrides_default():
    provider = resolve_provider(
        _settings(proxyapi_key="sk-proxy-real", openai_base_url="https://example.test/v1")
    )

    assert provider.base_url == "https://example.test/v1"


def test_live_mode_without_key_raises():
    with pytest.raises(ValueError, match="ключ"):
        get_llm_client(_settings())


def test_startup_log_has_provider_and_no_key():
    settings = _settings(proxyapi_key="sk-secret-must-not-appear")

    text = describe_llm(settings)

    assert "proxyapi" in text
    assert PROXY_BASE in text
    assert "sk-secret-must-not-appear" not in text
    assert describe_llm(Settings(llm_mode="mock")) == "llm: mock"


async def test_openai_timeout_becomes_llm_timeout():
    request = httpx.Request("POST", f"{OPENAI_BASE}/chat/completions")
    fake = _FakeCompletions(error=APITimeoutError(request=request))
    llm = OpenAILLM(_settings(openai_api_key="sk-test"), client=_FakeClient(fake))

    with pytest.raises(LLMTimeoutError):
        await llm.structure("оплатить хостинг")

    assert fake.calls
    assert fake.calls[0]["response_format"] == {"type": "json_object"}
    assert 0 <= fake.calls[0]["temperature"] <= 0.2
    assert fake.calls[0]["messages"][0]["role"] == "system"
    assert fake.calls[0]["messages"][1]["role"] == "user"
    assert fake.calls[0]["messages"][1]["content"] == "оплатить хостинг"


async def test_live_timeout_gives_review_and_audit_not_500(db_sessions, migrated_db):
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    request = httpx.Request("POST", f"{OPENAI_BASE}/chat/completions")
    fake = _FakeCompletions(error=APITimeoutError(request=request))
    settings = _settings(openai_api_key="sk-test", database_url=sqlite_url(migrated_db))
    live_app = create_app(settings)

    transport = ASGITransport(app=live_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        async with live_app.router.lifespan_context(live_app):
            live_app.state.llm = OpenAILLM(settings, client=_FakeClient(fake))
            response = await ac.post("/ai/structure", json={"text": "отправить договор"})

    assert response.status_code == 200
    assert response.json()["needs_review"] is True
    run = await last_run(db_sessions)
    assert run.error == ReviewCode.LLM_TIMEOUT
    assert run.status == "error"


async def test_connection_error_becomes_review_not_500():
    request = httpx.Request("POST", f"{OPENAI_BASE}/chat/completions")
    fake = _FakeCompletions(error=APIConnectionError(request=request, message="сеть недоступна"))
    llm = OpenAILLM(_settings(openai_api_key="sk-test"), client=_FakeClient(fake))

    from app.llm import LLMError

    with pytest.raises(LLMError):
        await llm.structure("купить кофе")


def _run_live_e2e() -> bool:
    """Живой вызов только по явной просьбе: иначе ключ в ОС сожжёт токены на каждом pytest."""
    flag = os.environ.get("LLM_E2E", "").strip().lower()
    if flag not in {"1", "true", "yes"}:
        return False
    try:
        resolve_provider(Settings())
    except ValueError:
        return False
    return True


@pytest.mark.skipif(not _run_live_e2e(), reason="нет ключа LLM или не задан LLM_E2E=1")
async def test_live_structure_optional_e2e():
    settings = Settings(llm_mode="live")
    llm = get_llm_client(settings)
    raw = await llm.structure("купить кофе и бумагу")

    assert raw.strip().startswith("{")
    assert "item_type" in raw
