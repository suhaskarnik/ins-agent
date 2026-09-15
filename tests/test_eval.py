"""Unit tests for the Judgment Eval Suite's comparison logic (ticket 18) —
the seams that don't require live Postgres/LLM infra. `evaluate_scenario`
itself (which replays a Scenario end-to-end) is exercised the same way as
`tests/test_scenarios.py`: skipped when that infra isn't available.
"""

import psycopg2
import pytest

from ins_agent.config import get_settings
from ins_agent.eval import (
    compare_eligibility_judgment,
    compare_sufficiency_assessment,
    evaluate_scenario,
)
from ins_agent.models.triage import EligibilityJudgment, SufficiencyAssessment
from ins_agent.scenarios import (
    list_scenario_ids,
    load_golden_eligibility_judgment,
    load_golden_sufficiency_assessment,
)


def test_compare_eligibility_judgment_matches_on_verdict_only():
    golden = EligibilityJudgment(eligible=True, rationale="golden rationale")
    actual = EligibilityJudgment(eligible=True, rationale="a differently-phrased rationale")

    assert compare_eligibility_judgment("tc001", golden, actual) == []


def test_compare_eligibility_judgment_flags_a_verdict_mismatch():
    golden = EligibilityJudgment(eligible=True, rationale="golden rationale")
    actual = EligibilityJudgment(eligible=False, rationale="golden rationale")

    mismatches = compare_eligibility_judgment("tc001", golden, actual)

    assert len(mismatches) == 1
    mismatch = mismatches[0]
    assert mismatch.scenario_id == "tc001"
    assert mismatch.step == "eligibility_judgment"
    assert mismatch.field_name == "eligible"
    assert mismatch.golden is True
    assert mismatch.actual is False


def test_compare_sufficiency_assessment_matches_regardless_of_rationale():
    golden = SufficiencyAssessment(
        sufficient=False, missing_documents=["repair_estimate"], rationale="golden rationale"
    )
    actual = SufficiencyAssessment(
        sufficient=False, missing_documents=["repair_estimate"], rationale="reworded rationale"
    )

    assert compare_sufficiency_assessment("tc006", golden, actual) == []


def test_compare_sufficiency_assessment_missing_documents_is_order_insensitive():
    golden = SufficiencyAssessment(
        sufficient=False,
        missing_documents=["repair_estimate", "police_report"],
        rationale="golden rationale",
    )
    actual = SufficiencyAssessment(
        sufficient=False,
        missing_documents=["police_report", "repair_estimate"],
        rationale="golden rationale",
    )

    assert compare_sufficiency_assessment("tc006", golden, actual) == []


def test_compare_sufficiency_assessment_flags_each_mismatched_field():
    golden = SufficiencyAssessment(
        sufficient=True, missing_documents=[], rationale="golden rationale"
    )
    actual = SufficiencyAssessment(
        sufficient=False,
        missing_documents=["repair_estimate"],
        rationale="golden rationale",
    )

    mismatches = compare_sufficiency_assessment("tc006", golden, actual)

    assert {m.field_name for m in mismatches} == {"sufficient", "missing_documents"}
    assert all(m.step == "sufficiency_assessment" for m in mismatches)


def test_golden_loaders_return_none_for_scenarios_that_never_reach_the_step():
    assert load_golden_eligibility_judgment("tc004") is None
    assert load_golden_sufficiency_assessment("tc004") is None
    assert load_golden_eligibility_judgment("tc005") is None
    assert load_golden_sufficiency_assessment("tc005") is None


def test_golden_loaders_load_recorded_output_for_scenarios_that_reach_the_step():
    golden = load_golden_eligibility_judgment("tc006")
    assert golden is not None
    assert golden.eligible is True

    golden_sufficiency = load_golden_sufficiency_assessment("tc006")
    assert golden_sufficiency is not None
    assert golden_sufficiency.sufficient is False
    assert golden_sufficiency.missing_documents == ["repair_estimate"]


def _infra_available() -> bool:
    try:
        settings = get_settings()
    except Exception:
        return False
    try:
        conn = psycopg2.connect(settings.postgres_dsn, connect_timeout=2)
        conn.close()
    except Exception:
        return False
    return True


@pytest.mark.skipif(
    not _infra_available(), reason="Postgres unavailable — run `just up && just seed` first"
)
@pytest.mark.parametrize("scenario_id", list_scenario_ids())
def test_evaluate_scenario_reports_no_drift_against_recorded_goldens(scenario_id):
    from ins_agent.checkpointer import get_checkpointer

    with get_checkpointer() as checkpointer:
        outcome = evaluate_scenario(scenario_id, checkpointer)

    assert outcome.mismatches == []
