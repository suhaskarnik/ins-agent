"""Loads a Scenario fixture (`data/tests/<id>/`) — a fixed Intake Input
paired with scripted human-gate responses, used to replay one branch of the
triage graph non-interactively and reproducibly.
"""

import json
from typing import Any

from ins_agent.models.claim import IntakeInput
from ins_agent.paths import REPO_ROOT

SCENARIOS_DIR = REPO_ROOT / "data" / "tests"


class Scenario:
    def __init__(self, scenario_id: str, intake: IntakeInput, gate_responses: list[str]):
        self.scenario_id = scenario_id
        self.intake = intake
        self._gate_responses = iter(gate_responses)

    def next_gate_response(self, _payload: dict[str, Any]) -> str:
        try:
            return next(self._gate_responses)
        except StopIteration as exc:
            raise RuntimeError(
                f"Scenario {self.scenario_id!r} hit an interrupt with no scripted "
                "response left in gate_responses.json"
            ) from exc


def load_scenario(scenario_id: str) -> Scenario:
    scenario_dir = SCENARIOS_DIR / scenario_id
    if not scenario_dir.is_dir():
        raise FileNotFoundError(f"No scenario fixture at {scenario_dir}")

    intake = IntakeInput.model_validate_json((scenario_dir / "intake_input.json").read_text())
    gate_responses = json.loads((scenario_dir / "gate_responses.json").read_text())

    return Scenario(scenario_id, intake, gate_responses)


def load_expected(scenario_id: str) -> dict[str, Any]:
    path = SCENARIOS_DIR / scenario_id / "expected.json"
    return json.loads(path.read_text())


def list_scenario_ids() -> list[str]:
    return sorted(p.name for p in SCENARIOS_DIR.iterdir() if p.is_dir())
