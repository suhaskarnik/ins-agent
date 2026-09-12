"""Unit tests for `route_after_rank`'s Broadening decision (ADR-0001) —
whether to loop back to Recall, proceed to Coverage Check, fall through to
the Policy Selection Gate, or fall through to the Final Review Gate. Pure
state-dict manipulation; no DB or LLM.
"""

from datetime import date
from decimal import Decimal

from ins_agent.models.policy import Policy
from ins_agent.models.triage import RankedCandidate
from ins_agent.nodes.rank import MAX_RECALL_ATTEMPTS, route_after_rank

POLICY = Policy(
    policy_id="POL-00002",
    holder_name="Brent Abbott",
    phone="940-781-6184",
    address="310 Kendra Common Apt. 164, Reidstad, GA 49021",
    dob=date(1964, 11, 2),
    product_type="Auto - Comprehensive",
    coverage_start=date(2025, 8, 4),
    coverage_end=date(2026, 4, 17),
    coverage_limit=Decimal("50000"),
    status="active",
)


def _candidate(score: float, **exact_flags: bool) -> RankedCandidate:
    return RankedCandidate(
        policy=POLICY,
        score=score,
        policy_id_exact=exact_flags.get("policy_id_exact", False),
        name_exact=exact_flags.get("name_exact", False),
        phone_exact=exact_flags.get("phone_exact", False),
        dob_exact=exact_flags.get("dob_exact", False),
    )


def test_resolved_policy_routes_to_coverage_check():
    state = {"resolved_policy": POLICY, "candidates": [_candidate(1.0)], "recall_attempt": 1}
    assert route_after_rank(state) == "coverage_check"


def test_nothing_above_threshold_loops_back_to_recall_when_attempts_remain():
    state = {"resolved_policy": None, "candidates": [_candidate(0.4)], "recall_attempt": 1}
    assert route_after_rank(state) == "recall"


def test_nothing_above_threshold_falls_through_once_attempts_are_exhausted():
    state = {
        "resolved_policy": None,
        "candidates": [_candidate(0.4)],
        "recall_attempt": MAX_RECALL_ATTEMPTS,
    }
    assert route_after_rank(state) == "notification"


def test_ambiguous_candidates_above_threshold_route_to_policy_selection_gate():
    state = {
        "resolved_policy": None,
        "candidates": [_candidate(0.8), _candidate(0.75)],
        "recall_attempt": 1,
    }
    assert route_after_rank(state) == "policy_selection_gate"


def test_no_candidates_at_all_loops_back_to_recall_when_attempts_remain():
    state = {"resolved_policy": None, "candidates": [], "recall_attempt": 1}
    assert route_after_rank(state) == "recall"


def test_no_candidates_at_all_falls_through_once_attempts_are_exhausted():
    state = {"resolved_policy": None, "candidates": [], "recall_attempt": MAX_RECALL_ATTEMPTS}
    assert route_after_rank(state) == "notification"


def test_multiple_candidates_still_below_threshold_route_to_policy_selection_gate_once_exhausted():
    state = {
        "resolved_policy": None,
        "candidates": [_candidate(0.4), _candidate(0.35)],
        "recall_attempt": MAX_RECALL_ATTEMPTS,
    }
    assert route_after_rank(state) == "policy_selection_gate"
