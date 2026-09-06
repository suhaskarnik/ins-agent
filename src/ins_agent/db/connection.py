"""Shared Postgres connection helper.

Every module that talks to Postgres (seed loading, the LLM cache, and later
the LangGraph checkpointer and Policy/Claim queries) connects through this
one function rather than calling `psycopg2.connect` with its own copy of the
DSN.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection as PgConnection

from ins_agent.config import get_settings


@contextmanager
def get_connection() -> Iterator[PgConnection]:
    """Yield a Postgres connection, closing it on exit.

    `psycopg2` connections are context managers themselves, but `__exit__`
    only commits/rolls back the transaction — it never closes the socket.
    Wrapping it here so `with get_connection() as conn:` closes the
    connection too, instead of every caller leaking one.
    """
    conn = psycopg2.connect(get_settings().postgres_dsn)
    try:
        yield conn
    finally:
        conn.close()
