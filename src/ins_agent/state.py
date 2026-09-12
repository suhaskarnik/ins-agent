"""The compiled graph's shared state.

Each node returns a partial dict of the fields it sets; LangGraph merges
them (last-write-wins per key — no node writes a key another node also
writes, so no reducer is needed).
"""

from typing import Literal, TypedDict

from ins_agent.models.claim import IntakeInput, PolicySearchQuery
from ins_agent.models.policy import Policy
from ins_agent.models.triage import (
    CoverageCheckResult,
    EligibilityJudgment,
    Notification,
    RankedCandidate,
    SufficiencyAssessment,
)


class TriageState(TypedDict, total=False):
    claim_id: str
    intake: IntakeInput

    raw_candidates: list[Policy]
    recall_attempt: int
    recall_query: PolicySearchQuery | None
    candidates: list[RankedCandidate]
    resolved_policy: Policy | None
    policy_resolution_confidence: float | None

    coverage_check: CoverageCheckResult | None
    eligibility_judgment: EligibilityJudgment | None
    sufficiency_assessment: SufficiencyAssessment | None

    notification: Notification | None
    final_decision: Literal["approve", "reject"] | None
