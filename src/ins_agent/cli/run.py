"""`just run` — interactively prompts for claim details, then runs the
triage graph end-to-end through the Final Review Gate."""

import uuid

from ins_agent.checkpointer import get_checkpointer
from ins_agent.cli.intake_prompt import prompt_intake_input
from ins_agent.graph import build_graph
from ins_agent.runner import run_to_completion
from ins_agent.tui import (
    prompt_approval,
    prompt_policy_selection,
    render_final_review_gate,
    render_policy_selection_gate,
)


def main() -> None:
    intake = prompt_intake_input()
    claim_id = f"claim-{uuid.uuid4().hex[:8]}"

    def on_interrupt(payload: dict) -> str:
        if payload["gate"] == "policy_selection":
            render_policy_selection_gate(payload)
            return prompt_policy_selection(payload)
        render_final_review_gate(payload)
        return prompt_approval()

    with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)
        result = run_to_completion(graph, claim_id, intake, on_interrupt)

    print(f"\nRun complete. Final decision: {result.get('final_decision')}")


if __name__ == "__main__":
    main()
