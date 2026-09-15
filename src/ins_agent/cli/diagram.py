"""`just diagram` — regenerates `docs/graph.mmd` directly from the compiled
LangGraph, so the diagram can never silently drift from the code. Also
re-embeds the same Mermaid source into ARCHITECTURE.md's ```mermaid fence,
so that copy can't drift from `docs/graph.mmd` either."""

import re

from ins_agent.graph import build_graph
from ins_agent.paths import REPO_ROOT

OUTPUT_PATH = REPO_ROOT / "docs" / "graph.mmd"
ARCHITECTURE_PATH = REPO_ROOT / "ARCHITECTURE.md"
MERMAID_FENCE = re.compile(r"```mermaid\n.*?\n```", re.DOTALL)


def _update_architecture_doc(mermaid: str) -> None:
    doc = ARCHITECTURE_PATH.read_text()
    fenced = f"```mermaid\n{mermaid.strip()}\n```"
    updated, count = MERMAID_FENCE.subn(fenced, doc, count=1)
    if count != 1:
        raise RuntimeError(f"Expected exactly one ```mermaid fence in {ARCHITECTURE_PATH}")
    ARCHITECTURE_PATH.write_text(updated)


def main() -> None:
    # No checkpointer needed: `draw_mermaid()` only inspects the compiled
    # graph's structure, never runs it, so this doesn't touch Postgres.
    graph = build_graph(None)
    mermaid = graph.get_graph().draw_mermaid()

    OUTPUT_PATH.write_text(mermaid)
    print(f"Wrote {OUTPUT_PATH}")

    _update_architecture_doc(mermaid)
    print(f"Updated {ARCHITECTURE_PATH}")


if __name__ == "__main__":
    main()
