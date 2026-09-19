"""Shared driver loop: invokes the compiled graph, presents interrupt
payloads, and resumes with a decision — used by both the interactive CLI
(`just run`) and the scripted Scenario runner (`just run-scenario`).

Each end-to-end run is traced as one Langfuse trace, named by claim/scenario
ID, via the LangChain Langfuse `CallbackHandler` passed to every invocation.
"""

import uuid
from collections.abc import Callable
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from ins_agent.models.claim import IntakeInput
from ins_agent.observability import get_langfuse_client
from ins_agent.state import TriageState

DecisionFn = Callable[[dict[str, Any]], str]


def run_to_completion(
    graph: CompiledStateGraph,
    claim_id: str,
    intake: IntakeInput,
    on_interrupt: DecisionFn,
    trace_name: str | None = None,
) -> TriageState:
    """Runs the graph from the start, resuming through every interrupt via
    `on_interrupt(payload) -> "approve" | "reject"`, until the run
    completes.

    Each call gets its own checkpointer thread (`claim_id` plus a random
    suffix) rather than reusing `claim_id` as the thread ID directly — the
    Postgres checkpointer persists state per thread, so replaying the same
    Scenario twice against the same thread would otherwise let a prior
    run's state leak into a fresh one wherever this run's routing skips a
    node the prior run executed.
    """
    thread_id = f"{claim_id}-{uuid.uuid4().hex[:8]}"
    get_langfuse_client()  # ensures the global client (config-derived) exists before handler init
    handler = CallbackHandler()
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
        "metadata": {"langfuse_trace_name": trace_name or f"triage:{claim_id}"},
    }

    initial_state: TriageState = {"claim_id": claim_id, "intake": intake}
    result = graph.invoke(initial_state, config=config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        decision = on_interrupt(payload)
        result = graph.invoke(Command(resume=decision), config=config)

    return cast(TriageState, result)
