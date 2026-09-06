"""`just diagram` — regenerates `docs/graph.mmd` directly from the compiled
LangGraph, so the diagram can never silently drift from the code."""

from ins_agent.graph import build_graph
from ins_agent.paths import REPO_ROOT

OUTPUT_PATH = REPO_ROOT / "docs" / "graph.mmd"


def main() -> None:
    # No checkpointer needed: `draw_mermaid()` only inspects the compiled
    # graph's structure, never runs it, so this doesn't touch Postgres.
    graph = build_graph(None)
    mermaid = graph.get_graph().draw_mermaid()

    OUTPUT_PATH.write_text(mermaid)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
