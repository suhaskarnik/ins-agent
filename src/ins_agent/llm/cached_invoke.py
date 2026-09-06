"""The single choke point every node uses to call an LLM.

`cached_invoke` is the only function in this codebase allowed to call
`.with_structured_output(...)` — no node talks to a provider SDK directly.
It enforces structured, Pydantic-validated output, serves repeated identical
calls from a content-addressed Postgres cache, retries transient provider
failures with backoff (and lets a still-failing call raise rather than
silently reaching the human as if it were a normal judgment outcome), and
logs a Langfuse generation span for every call — hit or miss — tagged
`cache_hit`.
"""

from typing import TypeVar

import groq
import openai
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ins_agent.config import get_settings
from ins_agent.db.cache import get_cached_response, store_response
from ins_agent.llm.hashing import cache_key, prompt_hash
from ins_agent.observability import get_langfuse_client

SchemaT = TypeVar("SchemaT", bound=BaseModel)

TRANSIENT_PROVIDER_ERRORS = (
    groq.APIConnectionError,
    groq.APITimeoutError,
    groq.RateLimitError,
    groq.InternalServerError,
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
)


def _model_id(model: BaseChatModel) -> str:
    model_name = getattr(model, "model_name", None) or getattr(model, "model", None)
    return f"{type(model).__name__}:{model_name}"


def _invoke_structured(model: BaseChatModel, schema: type[SchemaT], prompt: str) -> SchemaT:
    # `method="json_schema"` rather than the default (tool-calling): some
    # providers/models (observed with Groq's `openai/gpt-oss-*` models) are
    # unreliable at wrapping structured output in a forced tool call and
    # raise a 400 even when the underlying content is well-formed JSON.
    # json_schema mode asks for the same schema-validated output without
    # going through tool-choice enforcement.
    structured_model = model.with_structured_output(schema, method="json_schema")

    # Built per-call (not as a `@retry` decorator) so `max_retry_attempts`
    # is read from `Settings` fresh each time rather than baked in at
    # import time.
    retrying = Retrying(
        retry=retry_if_exception_type(TRANSIENT_PROVIDER_ERRORS),
        stop=stop_after_attempt(get_settings().max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    result = retrying(structured_model.invoke, prompt)
    assert isinstance(result, schema)
    return result


def cached_invoke(model: BaseChatModel, prompt: str, schema: type[SchemaT]) -> SchemaT:
    model_id = _model_id(model)
    schema_name = schema.__name__
    key = cache_key(model_id, prompt, schema_name)

    cached = get_cached_response(key)
    langfuse = get_langfuse_client()

    if cached is not None:
        with langfuse.start_as_current_observation(
            name="cached_invoke",
            as_type="generation",
            model=model_id,
            input=prompt,
            metadata={"cache_hit": True},
        ) as generation:
            result = schema.model_validate(cached)
            generation.update(output=result.model_dump(mode="json"))
        return result

    with langfuse.start_as_current_observation(
        name="cached_invoke",
        as_type="generation",
        model=model_id,
        input=prompt,
        metadata={"cache_hit": False},
    ) as generation:
        result = _invoke_structured(model, schema, prompt)
        response_json = result.model_dump(mode="json")
        store_response(key, model_id, prompt_hash(prompt), response_json)
        generation.update(output=response_json)

    return result
