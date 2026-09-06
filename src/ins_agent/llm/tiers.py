"""Model-tier factory.

Every node asks for a Model Tier (`model_fast` / `model_reasoning`) rather
than a concrete model name. This function is the only place that knows how
`LLM_PROVIDER` maps to a concrete LangChain chat model, so swapping providers
in `.env` never requires touching node code.
"""

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from ins_agent.config import get_settings

ModelTier = Literal["model_fast", "model_reasoning"]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_model(tier: ModelTier) -> BaseChatModel:
    settings = get_settings()
    model_name = getattr(settings, tier)

    if settings.llm_provider == "groq":
        return ChatGroq(model=model_name, api_key=SecretStr(settings.groq_api_key))

    if settings.llm_provider == "openrouter":
        assert settings.openrouter_api_key is not None
        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(settings.openrouter_api_key),
            base_url=OPENROUTER_BASE_URL,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
