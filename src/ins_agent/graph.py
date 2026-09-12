"""Builds and compiles the triage LangGraph.

Ticket 04's walking skeleton wired every node the pipeline ultimately
needs but only fully implemented tc001's clean-match path. Ticket 05 adds
the recall <-> rank Broadening loop (ADR-0001): `rank` may route back to
`recall` for another attempt when nothing clears the Match Threshold.
Multiple ambiguous candidates, or an exhausted Broadening budget, still
route straight to the Final Review Gate rather than through the Policy
Selection Gate — that's ticket 06's job to insert into this same shape.
"""

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ins_agent.nodes.coverage import coverage_check, route_after_coverage_check
from ins_agent.nodes.docs import sufficiency_assessment
from ins_agent.nodes.eligibility import eligibility_judgment, route_after_eligibility
from ins_agent.nodes.hitl import final_review_gate
from ins_agent.nodes.notification import draft_notification
from ins_agent.nodes.rank import rank, route_after_rank
from ins_agent.nodes.recall import recall
from ins_agent.state import TriageState


def build_graph(checkpointer: Any) -> CompiledStateGraph:
    builder = StateGraph(TriageState)

    builder.add_node("recall", recall)
    builder.add_node("rank", rank)
    builder.add_node("coverage_check", coverage_check)
    builder.add_node("eligibility_judgment", eligibility_judgment)
    builder.add_node("sufficiency_assessment", sufficiency_assessment)
    builder.add_node("notification", draft_notification)
    builder.add_node("final_review_gate", final_review_gate)

    builder.add_edge(START, "recall")
    builder.add_edge("recall", "rank")
    builder.add_conditional_edges(
        "rank", route_after_rank, ["coverage_check", "recall", "notification"]
    )
    builder.add_conditional_edges(
        "coverage_check", route_after_coverage_check, ["eligibility_judgment", "notification"]
    )
    builder.add_conditional_edges(
        "eligibility_judgment",
        route_after_eligibility,
        ["sufficiency_assessment", "notification"],
    )
    builder.add_edge("sufficiency_assessment", "notification")
    builder.add_edge("notification", "final_review_gate")
    builder.add_edge("final_review_gate", END)

    return builder.compile(checkpointer=checkpointer)
