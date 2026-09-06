"""Postgres-backed cache for structured LLM responses.

Keyed by a content-addressed hash (see `ins_agent.llm.hashing`), so entries
never go stale and there is no TTL — a changed model, prompt, or output
schema simply produces a different key rather than invalidating an old one.
"""

import json
from typing import Any

from ins_agent.db.connection import get_connection


def get_cached_response(cache_key: str) -> dict[str, Any] | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT response_json FROM llm_cache WHERE cache_key = %s", (cache_key,)
        )
        row = cur.fetchone()
    return row[0] if row else None


def store_response(
    cache_key: str, model: str, prompt_hash: str, response_json: dict[str, Any]
) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO llm_cache (cache_key, model, prompt_hash, response_json)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cache_key) DO NOTHING
            """,
            (cache_key, model, prompt_hash, json.dumps(response_json)),
        )
        conn.commit()


def clear_cache() -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE llm_cache")
        conn.commit()
