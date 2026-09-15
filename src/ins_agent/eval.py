"""Judgment Eval Suite (ticket 18): an on-demand drift check for the
Eligibility Judgment and Sufficiency Assessment steps.

Re-invokes those two judgment steps for each Scenario against `cached_invoke`
with the cache bypassed (so it reflects the *current* prompt/model rather
than a historical cached response) and compares the fresh structured output
to a recorded golden output field-by-field. Only the verdict fields are
asserted on (`eligible`, `sufficient`, `missing_documents`); free-text
`rationale` legitimately varies between calls and is never compared.

This is a smoke-test-sized drift signal, not a production eval framework —
see `ins_agent.cli.eval` for the caveats printed alongside every run. It is
deliberately separate from `just test`: a mismatch here is a signal for a
human to review, not a hard regression gate.
"""

from dataclasses import dataclass, field
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from ins_agent.graph import build_graph
from ins_agent.models.triage import EligibilityJudgment, SufficiencyAssessment
from ins_agent.nodes.docs import run_sufficiency_assessment
from ins_agent.nodes.eligibility import run_eligibility_judgment
from ins_agent.runner import run_to_completion
from ins_agent.scenarios import (
    load_golden_eligibility_judgment,
    load_golden_sufficiency_assessment,
    load_scenario,
)


@dataclass
class FieldMismatch:
    scenario_id: str
    step: str
    field_name: str
    golden: Any
    actual: Any


@dataclass
class ScenarioEvalOutcome:
    scenario_id: str
    checked_steps: list[str] = field(default_factory=list)
    mismatches: list[FieldMismatch] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def drifted(self) -> bool:
        return bool(self.mismatches)


def compare_eligibility_judgment(
    scenario_id: str, golden: EligibilityJudgment, actual: EligibilityJudgment
) -> list[FieldMismatch]:
    """Only `eligible` (the verdict) is compared. `rationale` is free text —
    logged by the caller, never asserted on."""
    if golden.eligible != actual.eligible:
        return [
            FieldMismatch(
                scenario_id, "eligibility_judgment", "eligible", golden.eligible, actual.eligible
            )
        ]
    return []


def compare_sufficiency_assessment(
    scenario_id: str, golden: SufficiencyAssessment, actual: SufficiencyAssessment
) -> list[FieldMismatch]:
    """`sufficient` and `missing_documents` are structured verdicts and are
    both compared (`missing_documents` order-insensitively). `rationale` is
    free text — logged by the caller, never asserted on."""
    mismatches = []
    if golden.sufficient != actual.sufficient:
        mismatches.append(
            FieldMismatch(
                scenario_id,
                "sufficiency_assessment",
                "sufficient",
                golden.sufficient,
                actual.sufficient,
            )
        )
    if set(golden.missing_documents) != set(actual.missing_documents):
        mismatches.append(
            FieldMismatch(
                scenario_id,
                "sufficiency_assessment",
                "missing_documents",
                golden.missing_documents,
                actual.missing_documents,
            )
        )
    return mismatches


def evaluate_scenario(scenario_id: str, checkpointer: Any) -> ScenarioEvalOutcome:
    """Replays a Scenario end-to-end (scripted gate responses, normal cache)
    to reach a resolved Policy/Coverage Check, then re-invokes whichever of
    Eligibility Judgment / Sufficiency Assessment that Scenario's graph run
    actually reached — this time with the cache bypassed — and diffs the
    fresh output against that Scenario's recorded golden output.
    """
    scenario = load_scenario(scenario_id)
    outcome = ScenarioEvalOutcome(scenario_id=scenario_id)

    graph: CompiledStateGraph = build_graph(checkpointer)
    state = run_to_completion(
        graph,
        claim_id=scenario.scenario_id,
        intake=scenario.intake,
        on_interrupt=scenario.next_gate_response,
        trace_name=f"eval:{scenario.scenario_id}",
    )

    if state.get("eligibility_judgment") is None:
        outcome.notes.append(
            "no Policy resolved or Coverage Check failed — Eligibility Judgment never runs"
        )
        return outcome

    golden_eligibility = load_golden_eligibility_judgment(scenario_id)
    if golden_eligibility is None:
        outcome.notes.append("no golden_eligibility_judgment.json recorded for this Scenario")
    else:
        actual_eligibility = run_eligibility_judgment(state, bypass_cache=True)
        outcome.checked_steps.append("eligibility_judgment")
        outcome.mismatches += compare_eligibility_judgment(
            scenario_id, golden_eligibility, actual_eligibility
        )

    if state.get("sufficiency_assessment") is None:
        outcome.notes.append("claim was ineligible — Sufficiency Assessment never runs")
        return outcome

    golden_sufficiency = load_golden_sufficiency_assessment(scenario_id)
    if golden_sufficiency is None:
        outcome.notes.append("no golden_sufficiency_assessment.json recorded for this Scenario")
    else:
        actual_sufficiency = run_sufficiency_assessment(state, bypass_cache=True)
        outcome.checked_steps.append("sufficiency_assessment")
        outcome.mismatches += compare_sufficiency_assessment(
            scenario_id, golden_sufficiency, actual_sufficiency
        )

    return outcome
