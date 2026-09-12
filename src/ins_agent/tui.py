"""Barebones `input()`-based TUI for the Policy Selection Gate and the
Final Review Gate.

Presentation only — the loop that invokes the graph and calls this lives in
`cli/run.py` (interactive) and `cli/run_scenario.py` (scripted).
"""

from typing import Any


def render_policy_selection_gate(payload: dict[str, Any]) -> str:
    lines = [
        "",
        "=" * 60,
        f"POLICY SELECTION GATE — claim {payload['claim_id']}",
        "=" * 60,
        "Multiple candidate Policies are ambiguously close — pick one, or decline.",
    ]

    for candidate in payload["candidates"]:
        matched = candidate["matched_fields"]
        lines.append("")
        lines.append(f"[{candidate['policy_id']}] score={candidate['score']:.3f}")
        lines.append(
            f"  holder_name: {candidate['holder_name']}  "
            f"({'match' if matched['holder_name'] else 'mismatch'})"
        )
        phone_match = "match" if matched["phone"] else "mismatch"
        lines.append(f"  phone:       {candidate['phone']}  ({phone_match})")
        dob_match = "match" if matched["dob"] else "mismatch"
        lines.append(f"  dob:         {candidate['dob']}  ({dob_match})")
        lines.append(f"  address:     {candidate['address']}")
        lines.append(f"  product:     {candidate['product_type']}  status: {candidate['status']}")
        lines.append(
            f"  coverage:    {candidate['coverage_start']} - {candidate['coverage_end']}, "
            f"limit {candidate['coverage_limit']}"
        )

    lines.append("=" * 60)

    text = "\n".join(lines)
    print(text)
    return text


def prompt_policy_selection(payload: dict[str, Any]) -> str:
    valid_ids = {candidate["policy_id"] for candidate in payload["candidates"]}
    while True:
        answer = input(
            f"Select a policy_id ({', '.join(sorted(valid_ids))}) or 'decline': "
        ).strip()
        if answer == "decline" or answer in valid_ids:
            return answer
        print(f"Please type one of {sorted(valid_ids)} or 'decline'.")


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
