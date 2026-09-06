"""Recall: finds candidate Policies from Intake Input.

This ticket's walking skeleton performs an exact-match lookup only — the
Intake Input's identifying fields become the Policy Search Query directly.
Fuzzy/LLM-driven Recall (constructing a looser query from messy input) is
ticket 05's concern; this function's signature (Intake Input in, Policies
out) is the seam that ticket will extend, not replace.
"""

from ins_agent.db.queries import find_policies_exact
from ins_agent.models.policy import Policy
from ins_agent.state import TriageState


def recall(state: TriageState) -> dict[str, list[Policy]]:
    query = state["intake"].search_query()
    return {"raw_candidates": find_policies_exact(query)}
