from contextlib import contextmanager
from unittest.mock import MagicMock

import groq
import httpx
import pytest
from pydantic import BaseModel

from ins_agent.llm import cached_invoke as cached_invoke_module
from ins_agent.llm.cached_invoke import cached_invoke
from ins_agent.llm.hashing import cache_key


class DummySchema(BaseModel):
    value: str


class FakeStructuredModel:
    def __init__(self, invoke_fn):
        self._invoke_fn = invoke_fn

    def invoke(self, prompt):
        return self._invoke_fn(prompt)


class FakeChatModel:
    model_name = "fake-model"

    def __init__(self, invoke_fn):
        self._invoke_fn = invoke_fn
        self.with_structured_output_calls: list[type] = []

    def with_structured_output(self, schema, **kwargs):
        self.with_structured_output_calls.append(schema)
        return FakeStructuredModel(self._invoke_fn)


class FakeGeneration:
    def __init__(self):
        self.updates: list[dict] = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


class FakeLangfuseClient:
    def __init__(self):
        self.observations: list[dict] = []

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        self.observations.append(kwargs)
        yield FakeGeneration()


@pytest.fixture(autouse=True)
def fake_langfuse(monkeypatch):
    client = FakeLangfuseClient()
    monkeypatch.setattr(cached_invoke_module, "get_langfuse_client", lambda: client)
    return client


def test_cache_hit_skips_the_model_and_returns_validated_object(monkeypatch, fake_langfuse):
    monkeypatch.setattr(
        cached_invoke_module, "get_cached_response", lambda key: {"value": "cached"}
    )
    store_mock = MagicMock()
    monkeypatch.setattr(cached_invoke_module, "store_response", store_mock)

    model = FakeChatModel(invoke_fn=lambda prompt: DummySchema(value="should-not-be-called"))

    result = cached_invoke(model, "find the policy", DummySchema)

    assert result == DummySchema(value="cached")
    assert model.with_structured_output_calls == []
    store_mock.assert_not_called()
    assert fake_langfuse.observations[0]["metadata"] == {"cache_hit": True}


def test_cache_miss_calls_the_model_and_stores_the_response(monkeypatch, fake_langfuse):
    monkeypatch.setattr(cached_invoke_module, "get_cached_response", lambda key: None)
    store_mock = MagicMock()
    monkeypatch.setattr(cached_invoke_module, "store_response", store_mock)

    model = FakeChatModel(invoke_fn=lambda prompt: DummySchema(value="fresh"))

    result = cached_invoke(model, "find the policy", DummySchema)

    assert result == DummySchema(value="fresh")
    assert model.with_structured_output_calls == [DummySchema]
    expected_key = cache_key("FakeChatModel:fake-model", "find the policy", "DummySchema")
    store_mock.assert_called_once()
    args, _ = store_mock.call_args
    assert args[0] == expected_key
    assert args[3] == {"value": "fresh"}
    assert fake_langfuse.observations[0]["metadata"] == {"cache_hit": False}


def test_transient_provider_errors_retry_then_succeed(monkeypatch, fake_langfuse):
    monkeypatch.setattr(cached_invoke_module, "get_cached_response", lambda key: None)
    monkeypatch.setattr(cached_invoke_module, "store_response", MagicMock())

    request = httpx.Request("POST", "https://groq.example.com")
    calls = {"count": 0}

    def flaky_invoke(prompt):
        calls["count"] += 1
        if calls["count"] < 3:
            raise groq.APIConnectionError(request=request)
        return DummySchema(value="succeeded-after-retry")

    model = FakeChatModel(invoke_fn=flaky_invoke)

    result = cached_invoke(model, "find the policy", DummySchema)

    assert result == DummySchema(value="succeeded-after-retry")
    assert calls["count"] == 3


def test_non_transient_errors_are_not_retried(monkeypatch, fake_langfuse):
    monkeypatch.setattr(cached_invoke_module, "get_cached_response", lambda key: None)
    monkeypatch.setattr(cached_invoke_module, "store_response", MagicMock())

    calls = {"count": 0}

    def always_fails(prompt):
        calls["count"] += 1
        raise ValueError("malformed structured output")

    model = FakeChatModel(invoke_fn=always_fails)

    with pytest.raises(ValueError):
        cached_invoke(model, "find the policy", DummySchema)

    assert calls["count"] == 1
