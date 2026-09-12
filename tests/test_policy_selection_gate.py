"""Unit tests for the Policy Selection Gate's decision handling and routing
(ticket 06). `interrupt()` itself needs a running graph/checkpointer to
call, so these exercise the pure pieces around it directly: resolving a
human's decision against the candidate list, and routing afterward. The
gate reached mid-run (and its durability across a restart) is covered by
the tc003 Scenario test instead.
"""

from datetime import date
from decimal import Decimal

import pytest

from ins_agent.models.policy import Policy
from ins_agent.models.triage import RankedCandidate
from ins_agent.nodes.hitl import _resolve_decision, route_after_policy_selection_gate

POLICY_A = Policy(
    policy_id="POL-00041",
    holder_name="Jordan Ellison",
    phone="212-555-0141",
    address="88 Corbin Row, Millhaven, OH 44107",
    dob=date(1979, 2, 14),
    product_type="Auto - Comprehensive",
    coverage_start=date(2025, 1, 1),
    coverage_end=date(2026, 1, 1),
    coverage_limit=Decimal("50000"),
    status="active",
)

POLICY_B = Policy(
    policy_id="POL-00042",
    holder_name="Jordan Ellison",
    phone="212-555-0142",
    address="410 Preston Alley, Millhaven, OH 44108",
    dob=date(1991, 7, 30),
    product_type="Auto - Liability",
    coverage_start=date(2025, 1, 1),
    coverage_end=date(2026, 1, 1),
    coverage_limit=Decimal("25000"),
    status="active",
)


def _candidate(policy: Policy, score: float) -> RankedCandidate:
    return RankedCandidate(
        policy=policy,
        score=score,
        policy_id_exact=False,
        name_exact=True,
        phone_exact=False,
        dob_exact=False,
    )


CANDIDATES = [_candidate(POLICY_A, 0.3), _candidate(POLICY_B, 0.3)]


def test_selecting_a_candidate_resolves_the_policy():
    result = _resolve_decision(CANDIDATES, "POL-00041")
    assert result["resolved_policy"] == POLICY_A
    assert result["policy_resolution_confidence"] == 0.3


def test_declining_leaves_the_policy_unresolved():
    result = _resolve_decision(CANDIDATES, "decline")
    assert result["resolved_policy"] is None
    assert result["policy_resolution_confidence"] is None


def test_unknown_decision_raises_rather_than_silently_defaulting():
    with pytest.raises(ValueError):
        _resolve_decision(CANDIDATES, "POL-99999")


def test_route_after_selecting_goes_to_coverage_check():
    state = {"resolved_policy": POLICY_A}
    assert route_after_policy_selection_gate(state) == "coverage_check"


def test_route_after_declining_goes_to_notification():
    state = {"resolved_policy": None}
    assert route_after_policy_selection_gate(state) == "notification"
