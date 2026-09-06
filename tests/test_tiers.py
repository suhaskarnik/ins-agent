from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from ins_agent.config import Settings
from ins_agent.llm.tiers import OPENROUTER_BASE_URL, get_model

BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "ins_agent",
    "POSTGRES_PASSWORD": "devpassword",
    "POSTGRES_DB": "ins_agent",
    "LANGFUSE_HOST": "https://langfuse.example.com",
    "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
    "LANGFUSE_SECRET_KEY": "sk-lf-test",
    "GROQ_API_KEY": "gsk_test",
    "MODEL_FAST": "fast-model",
    "MODEL_REASONING": "reasoning-model",
}


def _settings(monkeypatch, **overrides):
    env = {**BASE_ENV, **overrides}
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_groq_provider_resolves_to_chat_groq(monkeypatch):
    settings = _settings(monkeypatch, LLM_PROVIDER="groq")
    monkeypatch.setattr("ins_agent.llm.tiers.get_settings", lambda: settings)

    model = get_model("model_fast")

    assert isinstance(model, ChatGroq)
    assert model.model_name == "fast-model"


def test_openrouter_provider_resolves_to_chat_openai(monkeypatch):
    settings = _settings(
        monkeypatch, LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="or-test"
    )
    monkeypatch.setattr("ins_agent.llm.tiers.get_settings", lambda: settings)

    model = get_model("model_reasoning")

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "reasoning-model"
    assert model.openai_api_base == OPENROUTER_BASE_URL


def test_switching_provider_requires_no_code_change(monkeypatch):
    groq_settings = _settings(monkeypatch, LLM_PROVIDER="groq")
    monkeypatch.setattr("ins_agent.llm.tiers.get_settings", lambda: groq_settings)
    assert isinstance(get_model("model_fast"), ChatGroq)

    openrouter_settings = _settings(
        monkeypatch, LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="or-test"
    )
    monkeypatch.setattr("ins_agent.llm.tiers.get_settings", lambda: openrouter_settings)
    assert isinstance(get_model("model_fast"), ChatOpenAI)
