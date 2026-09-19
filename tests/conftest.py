"""Shared test doubles for Langfuse's client interface.

`FakeLangfuseClient` stands in for `get_langfuse_client()`'s return value
wherever a test needs to assert what got sent to Langfuse without a live
connection. `.log` (shared across instances/calls when passed in) records
span enter/exit markers by name, so a test can assert not just that a span
was opened, but that specific code ran *inside* it — see
`tests/test_eval.py`'s drift-check grouping tests.
"""

from contextlib import contextmanager


class FakeGeneration:
    def __init__(self):
        self.updates: list[dict] = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


class FakeLangfuseClient:
    def __init__(self, log: list[str] | None = None):
        self.observations: list[dict] = []
        self.last_generation: FakeGeneration | None = None
        self.log: list[str] = log if log is not None else []

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        self.observations.append(kwargs)
        self.last_generation = FakeGeneration()
        name = kwargs.get("name", "")
        self.log.append(f"span_enter:{name}")
        try:
            yield self.last_generation
        finally:
            self.log.append(f"span_exit:{name}")
