"""Coverage Check: deterministic — never blended with the Eligibility
Judgment. See ADR-0002."""

from ins_agent.models.triage import CoverageCheckResult
from ins_agent.state import TriageState


def coverage_check(state: TriageState) -> dict[str, CoverageCheckResult]:
    policy = state["resolved_policy"]
    assert policy is not None
    intake = state["intake"]

    within_coverage_limit = intake.requested_amount <= policy.coverage_limit
    within_coverage_window = policy.coverage_start <= intake.incident_date <= policy.coverage_end

    return {
        "coverage_check": CoverageCheckResult(
            within_coverage_limit=within_coverage_limit,
            within_coverage_window=within_coverage_window,
        )
    }


def route_after_coverage_check(state: TriageState) -> str:
    coverage = state["coverage_check"]
    assert coverage is not None
    # A failed Coverage Check already makes the claim ineligible (story 12)
    # — skip the reasoning-tier Eligibility Judgment call entirely rather
    # than compute and then discard it.
    return "eligibility_judgment" if coverage.covered else "notification"
