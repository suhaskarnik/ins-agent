"""Sufficiency Assessment: LLM call comparing the Claim's Submitted
Documents (structured metadata only, see ADR-0004) against the Guideline's
required set."""

from ins_agent.llm.cached_invoke import cached_invoke
from ins_agent.llm.tiers import get_model
from ins_agent.models.triage import SufficiencyAssessment
from ins_agent.prompts.loader import load_guideline, load_system_prompt
from ins_agent.state import TriageState


def _format_documents(intake_documents: list) -> str:
    if not intake_documents:
        return "(none submitted)"
    return "\n".join(
        f"- {doc.doc_type.value}: filename={doc.filename!r}, present={doc.present}"
        for doc in intake_documents
    )


def sufficiency_assessment(state: TriageState) -> dict[str, SufficiencyAssessment]:
    policy = state["resolved_policy"]
    assert policy is not None
    intake = state["intake"]

    prompt = load_system_prompt(
        "sufficiency_assessment",
        guideline=load_guideline("eligibility"),
        product_type=policy.product_type,
        description=intake.description,
        documents=_format_documents(intake.documents),
    )

    assessment = cached_invoke(get_model("model_fast"), prompt, SufficiencyAssessment)
    return {"sufficiency_assessment": assessment}
