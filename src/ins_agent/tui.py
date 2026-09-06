"""Barebones `input()`-based TUI for the Final Review Gate.

Presentation only — the loop that invokes the graph and calls this lives in
`cli/run.py` (interactive) and `cli/run_scenario.py` (scripted).
"""

from typing import Any


def render_final_review_gate(payload: dict[str, Any]) -> str:
    lines = [
        "",
        "=" * 60,
        f"FINAL REVIEW GATE — claim {payload['claim_id']}",
        "=" * 60,
    ]

    resolution = payload["policy_resolution"]
    lines.append("\n[deterministic fact] Policy Resolution")
    lines.append(f"  resolved:   {resolution['resolved']}")
    lines.append(f"  policy_id:  {resolution['policy_id']}")
    lines.append(f"  confidence: {resolution['confidence']}")

    coverage = payload["coverage_check"]
    lines.append("\n[deterministic fact] Coverage Check")
    if coverage:
        lines.append(f"  within coverage limit:  {coverage['within_coverage_limit']}")
        lines.append(f"  within coverage window: {coverage['within_coverage_window']}")
    else:
        lines.append("  not computed (Policy unresolved)")

    eligibility = payload["eligibility_judgment"]
    lines.append("\n[LLM judgment] Eligibility Judgment")
    if eligibility:
        lines.append(f"  eligible:  {eligibility['eligible']}")
        lines.append(f"  rationale: {eligibility['rationale']}")
    else:
        lines.append("  not assessed")

    sufficiency = payload["sufficiency_assessment"]
    lines.append("\n[LLM judgment] Sufficiency Assessment")
    if sufficiency:
        lines.append(f"  sufficient:         {sufficiency['sufficient']}")
        lines.append(f"  missing_documents:  {sufficiency['missing_documents']}")
        lines.append(f"  rationale:          {sufficiency['rationale']}")
    else:
        lines.append("  not assessed")

    notification = payload["notification"]
    lines.append("\nDrafted Notification")
    lines.append(f"  Subject: {notification['subject']}")
    lines.append(f"  {notification['body']}")
    lines.append("=" * 60)

    text = "\n".join(lines)
    print(text)
    return text


def prompt_approval() -> str:
    while True:
        answer = input("Approve or reject this claim? [approve/reject]: ").strip().lower()
        if answer in ("approve", "reject"):
            return answer
        print("Please type 'approve' or 'reject'.")
