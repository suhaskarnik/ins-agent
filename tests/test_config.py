import pytest
from pydantic import ValidationError

from ins_agent.config import Settings

BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "ins_agent",
    "POSTGRES_PASSWORD": "devpassword",
    "POSTGRES_DB": "ins_agent",
    "LANGFUSE_HOST": "https://langfuse.example.com",
    "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
    "LANGFUSE_SECRET_KEY": "sk-lf-test",
    "LLM_PROVIDER": "groq",
    "GROQ_API_KEY": "gsk_test",
    "MODEL_FAST": "fast-model",
    "MODEL_REASONING": "reasoning-model",
}


def _settings(monkeypatch, **overrides):
    env = {**BASE_ENV, **overrides}
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_loads_valid_env(monkeypatch):
    settings = _settings(monkeypatch)
    assert settings.postgres_host == "localhost"
    assert settings.llm_provider == "groq"
    assert settings.match_threshold == 0.7
    assert settings.top_n == 5
    assert settings.max_retry_attempts == 3


def test_missing_required_var_fails_fast(monkeypatch):
    env = dict(BASE_ENV)
    del env["GROQ_API_KEY"]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_malformed_var_fails_fast(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, POSTGRES_PORT="not-a-port")


def test_invalid_llm_provider_fails_fast(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, LLM_PROVIDER="bogus")


def test_openrouter_requires_its_own_key(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, LLM_PROVIDER="openrouter")

    settings = _settings(
        monkeypatch, LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="or-test"
    )
    assert settings.openrouter_api_key == "or-test"


def test_postgres_dsn(monkeypatch):
    settings = _settings(monkeypatch)
    assert settings.postgres_dsn == (
        "postgresql://ins_agent:devpassword@localhost:5432/ins_agent"
    )
