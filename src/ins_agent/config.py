"""Typed, validated access to the agent's `.env` configuration.

Every other module reads config through `get_settings()` rather than
`os.environ` directly, so a missing or malformed variable fails fast at
startup with one clear error instead of surfacing as a confusing exception
deep in a node.
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Postgres (policy/claim data, LangGraph checkpointer, LLM cache)
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # Langfuse observability
    langfuse_host: str
    langfuse_public_key: str
    langfuse_secret_key: str

    # LLM provider selection and credentials
    llm_provider: Literal["groq", "openrouter"]
    groq_api_key: str
    openrouter_api_key: str | None = None

    # Model tiers (concrete model name per tier, interpreted per-provider)
    model_fast: str
    model_reasoning: str

    # Policy Resolution tuning
    match_threshold: float = 0.7
    top_n: int = 5
    max_retry_attempts: int = 3

    @model_validator(mode="after")
    def _require_openrouter_key_when_selected(self) -> "Settings":
        if self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter"
            )
        return self

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


if __name__ == "__main__":
    settings = get_settings()
    print(
        settings.model_dump(
            exclude={
                "groq_api_key",
                "openrouter_api_key",
                "langfuse_secret_key",
                "postgres_password",
            }
        )
    )
