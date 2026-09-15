"""Eligibility Judgment: LLM call against `prompts/guidelines/eligibility.md`.

Reported as a field separate from the Coverage Check, never blended into
one verdict. See ADR-0002.
"""

from ins_agent.llm.cached_invoke import cached_invoke
from ins_agent.llm.tiers import get_model
from ins_agent.models.triage import EligibilityJudgment
from ins_agent.prompts.loader import load_guideline, load_system_prompt
from ins_agent.state import TriageState


def run_eligibility_judgment(
    state: TriageState, *, bypass_cache: bool = False
) -> EligibilityJudgment:
    """The Eligibility Judgment call itself, factored out of the node so
    `just eval` (ticket 18) can re-invoke it directly against a Scenario's
    already-resolved state, bypassing `cached_invoke`'s cache to check
    against the *current* prompt/model."""
    policy = state["resolved_policy"]
    coverage = state["coverage_check"]
    assert policy is not None
    assert coverage is not None
    intake = state["intake"]

    prompt = load_system_prompt(
        "eligibility_judgment",
        guideline=load_guideline("eligibility"),
        product_type=policy.product_type,
        policy_status=policy.status,
        coverage_start=str(policy.coverage_start),
        coverage_end=str(policy.coverage_end),
        coverage_limit=str(policy.coverage_limit),
        incident_date=str(intake.incident_date),
        description=intake.description,
        requested_amount=str(intake.requested_amount),
        within_coverage_limit=str(coverage.within_coverage_limit),
        within_coverage_window=str(coverage.within_coverage_window),
    )

    return cached_invoke(
        get_model("model_reasoning"), prompt, EligibilityJudgment, bypass_cache=bypass_cache
    )


def eligibility_judgment(state: TriageState) -> dict[str, EligibilityJudgment]:
    return {"eligibility_judgment": run_eligibility_judgment(state)}


def route_after_eligibility(state: TriageState) -> str:
    coverage = state["coverage_check"]
    judgment = state["eligibility_judgment"]
    assert coverage is not None
    assert judgment is not None
    if coverage.covered and judgment.eligible:
        return "sufficiency_assessment"
    return "notification"
