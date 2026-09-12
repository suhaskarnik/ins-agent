"""The two human-in-the-loop interrupts: the Policy Selection Gate and the
terminal Final Review Gate.

Policy Selection Gate (`policy_selection_gate`): reached when Rank leaves
multiple candidates unresolved (see `route_after_rank`) — every ambiguous
candidate is shown with its full field values, Rank Score, and which
specific fields matched or mismatched, so the human never has to pick from
a bare list of Policy IDs. The human either resumes with one candidate's
`policy_id` (which becomes the resolved Policy) or with `"decline"`, which
leaves the Policy unresolved and proceeds straight to the Final Review Gate
exactly like any other unresolved-Policy run — not a crash or silent
default.

Final Review Gate (`final_review_gate`): the terminal interrupt. Presents
Policy Resolution confidence, the Coverage Check result, the Eligibility
Judgment, and the Sufficiency Assessment — each labeled deterministic fact
or LLM judgment — plus the drafted Notification. Approving writes the
Notification to disk; rejecting ends the run with nothing written. No
edit-and-resubmit loop — approve/reject only.

Both interrupts pause via LangGraph's `interrupt()`, which durably survives
a process restart through the Postgres checkpointer — see ADR-0003.
"""

from typing import Any

from langgraph.types import interrupt

from ins_agent.models.triage import RankedCandidate
from ins_agent.output import write_notification
from ins_agent.state import TriageState


def _candidate_payload(candidate: RankedCandidate) -> dict[str, Any]:
    policy = candidate.policy
    return {
        "policy_id": policy.policy_id,
        "holder_name": policy.holder_name,
        "phone": policy.phone,
        "address": policy.address,
        "dob": policy.dob.isoformat(),
        "product_type": policy.product_type,
        "coverage_start": policy.coverage_start.isoformat(),
        "coverage_end": policy.coverage_end.isoformat(),
        "coverage_limit": str(policy.coverage_limit),
        "status": policy.status,
        "score": candidate.score,
        "matched_fields": {
            "policy_id": candidate.policy_id_exact,
            "holder_name": candidate.name_exact,
            "phone": candidate.phone_exact,
            "dob": candidate.dob_exact,
        },
    }


def _resolve_decision(
    candidates: list[RankedCandidate], decision: str
) -> dict[str, Any]:
    if decision == "decline":
        return {"resolved_policy": None, "policy_resolution_confidence": None}

    selected = next((c for c in candidates if c.policy.policy_id == decision), None)
    if selected is None:
        raise ValueError(
            f"Policy Selection Gate: decision {decision!r} is neither 'decline' nor "
            f"one of the candidate policy_ids {[c.policy.policy_id for c in candidates]!r}"
        )
    return {"resolved_policy": selected.policy, "policy_resolution_confidence": selected.score}


def policy_selection_gate(state: TriageState) -> dict[str, Any]:
    candidates = state.get("candidates") or []
    payload = {
        "gate": "policy_selection",
        "claim_id": state["claim_id"],
        "candidates": [_candidate_payload(c) for c in candidates],
    }
    decision = interrupt(payload)
    return _resolve_decision(candidates, decision)


def route_after_policy_selection_gate(state: TriageState) -> str:
    return "coverage_check" if state.get("resolved_policy") else "notification"


def _build_payload(state: TriageState) -> dict[str, Any]:
    policy = state.get("resolved_policy")
    coverage = state.get("coverage_check")
    eligibility = state.get("eligibility_judgment")
    sufficiency = state.get("sufficiency_assessment")
    notification = state["notification"]
    assert notification is not None

    return {
        "gate": "final_review",
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
