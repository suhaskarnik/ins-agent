"""Notification: LLM-drafted customer-facing message, presented at the
Final Review Gate. Never sent — see CONTEXT.md."""

from ins_agent.llm.cached_invoke import cached_invoke
from ins_agent.llm.tiers import get_model
from ins_agent.models.triage import Notification
from ins_agent.prompts.loader import load_system_prompt
from ins_agent.state import TriageState


def draft_notification(state: TriageState) -> dict[str, Notification]:
    intake = state["intake"]
    coverage = state.get("coverage_check")
    eligibility = state.get("eligibility_judgment")
    sufficiency = state.get("sufficiency_assessment")

    prompt = load_system_prompt(
        "notification_drafting",
        policy_resolved=str(state.get("resolved_policy") is not None),
        covered=str(coverage.covered) if coverage else "not applicable",
        eligible=str(eligibility.eligible) if eligibility else "not applicable",
        sufficient=str(sufficiency.sufficient) if sufficiency else "not applicable",
        claimant_name=intake.claimant_name,
        incident_date=str(intake.incident_date),
        requested_amount=str(intake.requested_amount),
    )

    notification = cached_invoke(get_model("model_reasoning"), prompt, Notification)
    return {"notification": notification}
