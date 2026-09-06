"""Final Review Gate: the terminal human-in-the-loop interrupt.

Presents Policy Resolution confidence, the Coverage Check result, the
Eligibility Judgment, and the Sufficiency Assessment — each labeled
deterministic fact or LLM judgment — plus the drafted Notification.
Approving writes the Notification to disk; rejecting ends the run with
nothing written. No edit-and-resubmit loop — approve/reject only.
"""

from typing import Any

from langgraph.types import interrupt

from ins_agent.output import write_notification
from ins_agent.state import TriageState


def _build_payload(state: TriageState) -> dict[str, Any]:
    policy = state.get("resolved_policy")
    coverage = state.get("coverage_check")
    eligibility = state.get("eligibility_judgment")
    sufficiency = state.get("sufficiency_assessment")
    notification = state["notification"]
    assert notification is not None

    return {
        "claim_id": state["claim_id"],
        "policy_resolution": {
            "kind": "deterministic",
            "resolved": policy is not None,
            "policy_id": policy.policy_id if policy else None,
            "confidence": state.get("policy_resolution_confidence"),
        },
        "coverage_check": {
            "kind": "deterministic",
            "within_coverage_limit": coverage.within_coverage_limit if coverage else None,
            "within_coverage_window": coverage.within_coverage_window if coverage else None,
        }
        if coverage
        else None,
        "eligibility_judgment": {
            "kind": "llm_judgment",
            "eligible": eligibility.eligible,
            "rationale": eligibility.rationale,
        }
        if eligibility
        else None,
        "sufficiency_assessment": {
            "kind": "llm_judgment",
            "sufficient": sufficiency.sufficient,
            "missing_documents": sufficiency.missing_documents,
            "rationale": sufficiency.rationale,
        }
        if sufficiency
        else None,
        "notification": {
            "subject": notification.subject,
            "body": notification.body,
        },
    }


def final_review_gate(state: TriageState) -> dict[str, str]:
    payload = _build_payload(state)
    decision = interrupt(payload)

    if decision == "approve":
        write_notification(state["claim_id"], state["notification"])  # type: ignore[arg-type]

    return {"final_decision": decision}
