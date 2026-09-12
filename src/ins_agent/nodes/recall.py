"""Recall: finds candidate Policies from Intake Input.

Ticket 04's exact-match lookup is now attempt 1 of a fixed, deterministic
Broadening sequence (see ADR-0001): an LLM call first builds a structured
`PolicySearchQuery` from Intake Input via `cached_invoke` (never freeform
text or SQL) on attempt 1 only; that same query is then loosened on later
attempts rather than re-asked of the LLM. Attempt 2 drops DOB/phone (keeps
policy_id + name, both exact); attempt 3 falls back to name-only fuzzy
matching. `route_after_rank` decides whether another attempt is warranted
and loops back to this node — this module has no opinion on that, and
enforces nothing beyond what a single attempt does.
"""

from ins_agent.db.queries import find_policies_exact, find_policies_fuzzy_name
from ins_agent.llm.cached_invoke import cached_invoke
from ins_agent.llm.tiers import get_model
from ins_agent.models.claim import PolicySearchQuery
from ins_agent.models.policy import Policy
from ins_agent.prompts.loader import load_system_prompt
from ins_agent.state import TriageState

MAX_RECALL_ATTEMPTS = 3


def _build_query(state: TriageState) -> PolicySearchQuery:
    intake = state["intake"]
    prompt = load_system_prompt(
        "recall_query",
        policy_id=intake.policy_id or "",
        holder_name=intake.holder_name or "",
        phone=intake.phone or "",
        dob=str(intake.dob) if intake.dob else "",
    )
    return cached_invoke(get_model("model_fast"), prompt, PolicySearchQuery)


def recall(state: TriageState) -> dict[str, list[Policy] | int | PolicySearchQuery]:
    attempt = state.get("recall_attempt", 0) + 1

    if attempt == 1:
        query = _build_query(state)
        candidates = find_policies_exact(query)
    else:
        stored_query = state["recall_query"]
        assert stored_query is not None
        query = stored_query
        if attempt == 2:
            broadened = query.model_copy(update={"phone": None, "dob": None})
            candidates = find_policies_exact(broadened)
        else:
            candidates = (
                find_policies_fuzzy_name(query.holder_name, policy_id=query.policy_id)
                if query.holder_name
                else []
            )

    return {"raw_candidates": candidates, "recall_attempt": attempt, "recall_query": query}
