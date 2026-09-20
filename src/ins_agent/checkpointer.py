"""Postgres-backed LangGraph checkpointer.

Both human-in-the-loop interrupts (Policy Selection Gate, Final Review
Gate) need a durable checkpointer so a paused run survives a process
restart — see ADR-0003. Uses the same local Postgres instance as
Policy/Claim data and the LLM cache.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from ins_agent.config import get_settings
from ins_agent.models.claim import Claim, DocType, Document, IntakeInput, PolicySearchQuery
from ins_agent.models.policy import Policy
from ins_agent.models.triage import (
    CoverageCheckResult,
    EligibilityJudgment,
    Notification,
    RankedCandidate,
    SufficiencyAssessment,
)

# Graph state is built out of these Pydantic models/enums, which round-trip
# through msgpack on every checkpoint. Without an explicit allowlist entry
# LangGraph will refuse to deserialize them once LANGGRAPH_STRICT_MSGPACK
# becomes the default.
_CHECKPOINTED_TYPES = [
    Claim,
    Document,
    DocType,
    IntakeInput,
    PolicySearchQuery,
    Policy,
    CoverageCheckResult,
    EligibilityJudgment,
    Notification,
    RankedCandidate,
    SufficiencyAssessment,
]


@contextmanager
def get_checkpointer() -> Iterator[PostgresSaver]:
    with PostgresSaver.from_conn_string(get_settings().postgres_dsn) as saver:
        saver.setup()
        # The default serde's allowed_msgpack_modules is `True` (warn-but-allow),
        # and with_allowlist() is a no-op against that state — it only merges
        # into an *explicit* allowlist. So we replace the serde outright with
        # one scoped to exactly the types our graph state uses.
        saver.serde = JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINTED_TYPES)
        yield saver
