"""`just run-scenario <id>` — replays a Scenario's Intake Input
non-interactively, end-to-end through approval, using its scripted gate
responses instead of `input()`."""

import sys

from ins_agent.checkpointer import get_checkpointer
from ins_agent.graph import build_graph
from ins_agent.runner import run_to_completion
from ins_agent.scenarios import load_scenario
from ins_agent.tui import render_final_review_gate, render_policy_selection_gate


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: run_scenario <scenario_id>", file=sys.stderr)
        raise SystemExit(2)

    scenario = load_scenario(sys.argv[1])

    def on_interrupt(payload: dict) -> str:
        if payload["gate"] == "policy_selection":
            render_policy_selection_gate(payload)
        else:
            render_final_review_gate(payload)
        decision = scenario.next_gate_response(payload)
        print(f"(scripted response: {decision})")
        return decision

    with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)
        result = run_to_completion(
            graph,
            claim_id=scenario.scenario_id,
            intake=scenario.intake,
            on_interrupt=on_interrupt,
            trace_name=scenario.scenario_id,
        )

    print(
        f"\nScenario {scenario.scenario_id} complete. Final decision: "
        f"{result.get('final_decision')}"
    )


if __name__ == "__main__":
    main()
