"""`just eval` — a drift check for the Eligibility Judgment / Sufficiency
Assessment steps, separate from `just test` (see `ins_agent.eval`).

Exits non-zero when drift is found so a caller can notice, but this is
deliberately not wired into `just test`/CI: an LLM judgment call can
legitimately drift in ways that don't warrant blocking a merge, and this
suite's golden set is too small to be a hard gate.
"""

import sys

from ins_agent.checkpointer import get_checkpointer
from ins_agent.eval import evaluate_scenario
from ins_agent.scenarios import list_scenario_ids

HEADER = """\
Judgment Eval Suite — drift check for Eligibility Judgment / Sufficiency Assessment
====================================================================================
This is NOT a production eval framework. Specifically, it is not:
  - a golden set larger than the existing 6 hand-picked Scenarios
  - human-adjudicated ground truth (the golden output is the original
    author's judgment at recording time)
  - drift-over-time tracking (this is a single point-in-time comparison
    against whatever golden output currently exists)
  - a source of statistical confidence (pass/fail on individual fields only)

A mismatch below is a signal for a human to review, not a hard regression —
LLM outputs can legitimately vary in phrasing even when the verdict holds.
"""


def main() -> None:
    print(HEADER)

    any_mismatch = False
    with get_checkpointer() as checkpointer:
        for scenario_id in list_scenario_ids():
            outcome = evaluate_scenario(scenario_id, checkpointer)

            if outcome.mismatches:
                any_mismatch = True
                for mismatch in outcome.mismatches:
                    print(
                        f"[{scenario_id}] DRIFT in {mismatch.step}.{mismatch.field_name}: "
                        f"golden={mismatch.golden!r} actual={mismatch.actual!r}"
                    )
            elif outcome.checked_steps:
                checked = ", ".join(outcome.checked_steps)
                print(f"[{scenario_id}] OK — {checked} match golden output")
            else:
                print(f"[{scenario_id}] skipped")

            for note in outcome.notes:
                print(f"[{scenario_id}] note: {note}")

    if any_mismatch:
        print("\nDrift detected — review the scenarios above.")
        sys.exit(1)

    print("\nNo drift detected.")


if __name__ == "__main__":
    main()
