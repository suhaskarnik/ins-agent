"""Rank: deterministic weighted scoring of Recall's candidates, and
auto-resolution when the result is unambiguous.

Auto-resolves to a single Policy on a Perfect Score, or when exactly one
candidate clears the Match Threshold with no other candidate also clearing
it. When nothing clears the threshold and Recall's Broadening budget
(`MAX_RECALL_ATTEMPTS`, ADR-0001) isn't exhausted, routes back to Recall for
another attempt. Anything else left unresolved (multiple ambiguous
candidates, or a broadening budget that's exhausted) routes straight to the
Final Review Gate — the Policy Selection Gate (ticket 06) will replace that
fallback.
"""

from ins_agent.config import get_settings
from ins_agent.matching.rank import rank_score
from ins_agent.models.policy import Policy
from ins_agent.models.triage import RankedCandidate
from ins_agent.nodes.recall import MAX_RECALL_ATTEMPTS
from ins_agent.state import TriageState


def _auto_resolve(candidates: list[RankedCandidate], threshold: float) -> RankedCandidate | None:
    perfect = [c for c in candidates if c.is_perfect]
    if len(perfect) == 1:
        return perfect[0]

    above_threshold = [c for c in candidates if c.score >= threshold]
    if len(above_threshold) == 1:
        return above_threshold[0]

    return None


def rank(state: TriageState) -> dict[str, list[RankedCandidate] | Policy | float | None]:
    query = state["intake"].search_query()
    raw_candidates = state["raw_candidates"]
    candidates = [rank_score(policy, query) for policy in raw_candidates]

    resolved = _auto_resolve(candidates, get_settings().match_threshold)

    return {
        "candidates": candidates,
        "resolved_policy": resolved.policy if resolved else None,
        "policy_resolution_confidence": resolved.score if resolved else None,
    }


def route_after_rank(state: TriageState) -> str:
    if state.get("resolved_policy"):
        return "coverage_check"

    candidates = state.get("candidates") or []
    threshold = get_settings().match_threshold
    cleared_threshold = any(c.score >= threshold for c in candidates)
    attempt = state.get("recall_attempt", 0)

    if not cleared_threshold and attempt < MAX_RECALL_ATTEMPTS:
        return "recall"
    return "notification"
