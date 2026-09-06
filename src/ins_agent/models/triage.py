"""Outputs produced by each stage of the triage graph.

Each model is documented as either a deterministic fact or an LLM judgment
so the Final Review Gate can label them accordingly rather than blending
them — see CONTEXT.md and ADR-0002.
"""

from pydantic import BaseModel

from ins_agent.models.policy import Policy


class RankedCandidate(BaseModel):
    """Deterministic. One Policy scored against an Intake Input by Rank."""

    policy: Policy
    score: float
    policy_id_exact: bool
    name_exact: bool
    phone_exact: bool
    dob_exact: bool

    @property
    def is_perfect(self) -> bool:
        return self.policy_id_exact and self.name_exact


class CoverageCheckResult(BaseModel):
    """Deterministic. Requested amount vs. coverage limit, incident date vs.
    coverage window."""

    within_coverage_limit: bool
    within_coverage_window: bool

    @property
    def covered(self) -> bool:
        return self.within_coverage_limit and self.within_coverage_window


class EligibilityJudgment(BaseModel):
    """LLM judgment, against `prompts/guidelines/eligibility.md`."""

    eligible: bool
    rationale: str


class SufficiencyAssessment(BaseModel):
    """LLM judgment, Submitted Documents vs. the Guideline's required set."""

    sufficient: bool
    missing_documents: list[str]
    rationale: str


class Notification(BaseModel):
    """LLM-drafted, never sent — written to disk only on approval."""

    subject: str
    body: str
