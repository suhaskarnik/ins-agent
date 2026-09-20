"""Scenario tests: each fixture under `data/tests/<id>/` pairs a fixed
Intake Input with scripted gate responses and an expected terminal outcome.
A single parametrized test invokes the compiled graph (against the seeded
Postgres + checkpointer, and real LLM calls behind `cached_invoke`) and
asserts only on the terminal state — never on intermediate node internals.

Requires a running, seeded Postgres and working LLM credentials (see
`just up` / `just seed`); skipped when Postgres isn't reachable. Marked
`integration` and excluded from CI (`pytest -m "not integration"`), since
CI has no route to a real LLM provider or self-hosted Langfuse instance —
run these locally instead.
"""

import psycopg2
import pytest

from ins_agent.checkpointer import get_checkpointer
from ins_agent.config import get_settings
from ins_agent.graph import build_graph
from ins_agent.runner import run_to_completion
from ins_agent.scenarios import list_scenario_ids, load_expected, load_scenario


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


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _infra_available(), reason="Postgres unavailable — run `just up && just seed` first"
    ),
]


@pytest.mark.parametrize("scenario_id", list_scenario_ids())
def test_scenario_reaches_expected_terminal_outcome(scenario_id: str):
    scenario = load_scenario(scenario_id)
    expected = load_expected(scenario_id)

    with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)
        result = run_to_completion(
            graph,
            claim_id=scenario.scenario_id,
            intake=scenario.intake,
            on_interrupt=scenario.next_gate_response,
            trace_name=scenario.scenario_id,
        )

    resolved_policy = result.get("resolved_policy")
    assert (resolved_policy.policy_id if resolved_policy else None) == expected[
        "resolved_policy_id"
    ]
    assert result.get("policy_resolution_confidence") == expected["policy_resolution_confidence"]

    coverage = result.get("coverage_check")
    assert (coverage.covered if coverage else None) == expected["coverage_check_covered"]

    eligibility = result.get("eligibility_judgment")
    assert (eligibility.eligible if eligibility else None) == expected[
        "eligibility_judgment_eligible"
    ]

    sufficiency = result.get("sufficiency_assessment")
    assert (sufficiency.sufficient if sufficiency else None) == expected[
        "sufficiency_assessment_sufficient"
    ]

    assert result.get("final_decision") == expected["final_decision"]
