"""Langfuse client, configured from `Settings` rather than ambient env vars.

Every other module reads Postgres/LLM config through `get_settings()`
instead of `os.environ`; the Langfuse client follows the same rule.
"""

from functools import lru_cache

from langfuse import Langfuse

from ins_agent.config import get_settings


@lru_cache
def get_langfuse_client() -> Langfuse:
    settings = get_settings()
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
