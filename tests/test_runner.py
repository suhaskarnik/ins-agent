from unittest.mock import MagicMock

from ins_agent import runner as runner_module
from ins_agent.runner import run_to_completion


class FakeGraph:
    def __init__(self, result):
        self._result = result
        self.invoke_calls: list[dict] = []

    def invoke(self, state, config):
        self.invoke_calls.append({"state": state, "config": config})
        return self._result


def test_run_to_completion_names_the_trace_via_the_v4_metadata_key(monkeypatch):
    monkeypatch.setattr(runner_module, "get_langfuse_client", lambda: MagicMock())
    monkeypatch.setattr(runner_module, "CallbackHandler", MagicMock())

    graph = FakeGraph(result={"claim_id": "tc003"})
    run_to_completion(graph, "tc003", intake=object(), on_interrupt=lambda payload: "approve")

    metadata = graph.invoke_calls[0]["config"]["metadata"]

    assert metadata["langfuse_trace_name"] == "triage:tc003"
    assert "langfuse_session_name" not in metadata


def test_run_to_completion_honors_an_explicit_trace_name(monkeypatch):
    monkeypatch.setattr(runner_module, "get_langfuse_client", lambda: MagicMock())
    monkeypatch.setattr(runner_module, "CallbackHandler", MagicMock())

    graph = FakeGraph(result={"claim_id": "custom"})
    run_to_completion(
        graph,
        "custom",
        intake=object(),
        on_interrupt=lambda payload: "approve",
        trace_name="my-trace",
    )

    metadata = graph.invoke_calls[0]["config"]["metadata"]
    assert metadata["langfuse_trace_name"] == "my-trace"
