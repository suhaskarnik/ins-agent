"""Postgres-backed LangGraph checkpointer.

Both human-in-the-loop interrupts (Policy Selection Gate, Final Review
Gate) need a durable checkpointer so a paused run survives a process
restart — see ADR-0003. Uses the same local Postgres instance as
Policy/Claim data and the LLM cache.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver

from ins_agent.config import get_settings


@contextmanager
def get_checkpointer() -> Iterator[PostgresSaver]:
    with PostgresSaver.from_conn_string(get_settings().postgres_dsn) as saver:
        saver.setup()
        yield saver
