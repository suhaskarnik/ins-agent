"""The single choke point every node uses to call an LLM.

`cached_invoke` is the only function in this codebase allowed to call
`.with_structured_output(...)` — no node talks to a provider SDK directly.
It enforces structured, Pydantic-validated output, serves repeated identical
calls from a content-addressed Postgres cache, retries transient provider
failures with backoff (and lets a still-failing call raise rather than
silently reaching the human as if it were a normal judgment outcome), and
logs a Langfuse generation span for every call — hit or miss — tagged
`cache_hit`, with token `usage_details` attached (zeroed on a cache hit,
since no provider call was made) so Langfuse can price it.
"""

from dataclasses import dataclass
from typing import Any, TypeVar, cast

import groq
import openai
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ValidationError
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ins_agent.config import get_settings
from ins_agent.db.cache import get_cached_response, store_response
from ins_agent.llm.hashing import cache_key, prompt_hash
from ins_agent.observability import get_langfuse_client

SchemaT = TypeVar("SchemaT", bound=BaseModel)

ZERO_USAGE_DETAILS = {"input": 0, "output": 0}


@dataclass
class StructuredResult[SchemaT: BaseModel]:
    parsed: SchemaT
    usage_details: dict[str, int]


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


def _usage_details(raw_message) -> dict[str, int]:
    usage = getattr(raw_message, "usage_metadata", None) or {}
    return {
        "input": usage.get("input_tokens", 0),
        "output": usage.get("output_tokens", 0),
    }


def _invoke_structured(
    model: BaseChatModel, schema: type[SchemaT], prompt: str
) -> StructuredResult[SchemaT]:
    # `method="json_schema"` rather than the default (tool-calling): some
    # providers/models (observed with Groq's `openai/gpt-oss-*` models) are
    # unreliable at wrapping structured output in a forced tool call and
    # raise a 400 even when the underlying content is well-formed JSON.
    # json_schema mode asks for the same schema-validated output without
    # going through tool-choice enforcement.
    #
    # `include_raw=True` so the raw `AIMessage` (and its `usage_metadata`)
    # survives alongside the validated object — needed to report token
    # usage/cost to Langfuse.
    structured_model = model.with_structured_output(schema, method="json_schema", include_raw=True)

    # Built per-call (not as a `@retry` decorator) so `max_retry_attempts`
    # is read from `Settings` fresh each time rather than baked in at
    # import time.
    retrying = Retrying(
        retry=retry_if_exception_type(TRANSIENT_PROVIDER_ERRORS),
        stop=stop_after_attempt(get_settings().max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    response = cast(dict[str, Any], retrying(structured_model.invoke, prompt))
    if response["parsing_error"] is not None:
        raise response["parsing_error"]
    parsed = response["parsed"]
    assert isinstance(parsed, schema)
    return StructuredResult(parsed=parsed, usage_details=_usage_details(response["raw"]))


def cached_invoke(model: BaseChatModel, prompt: str, schema: type[SchemaT]) -> SchemaT:
    model_id = _model_id(model)
    schema_name = schema.__name__
    key = cache_key(model_id, prompt, schema_name)

    cached = get_cached_response(key)
    langfuse = get_langfuse_client()

    if cached is not None:
        try:
            result = schema.model_validate(cached)
        except ValidationError:
            # The cached row was written against an older shape of `schema`
            # (e.g. a newly added required field) but `cache_key` doesn't
            # encode the schema's field shape, so the stale row still hits.
            # Treat it as a miss rather than surfacing a validation error to
            # the caller; the fresh response below overwrites this key.
            pass
        else:
            with langfuse.start_as_current_observation(
                name="cached_invoke",
                as_type="generation",
                model=model_id,
                input=prompt,
                metadata={"cache_hit": True},
            ) as generation:
                generation.update(
                    output=result.model_dump(mode="json"), usage_details=ZERO_USAGE_DETAILS
                )
            return result

    with langfuse.start_as_current_observation(
        name="cached_invoke",
        as_type="generation",
        model=model_id,
        input=prompt,
        metadata={"cache_hit": False},
    ) as generation:
        try:
            structured = _invoke_structured(model, schema, prompt)
        except Exception as exc:
            generation.update(level="ERROR", status_message=str(exc))
            raise
        response_json = structured.parsed.model_dump(mode="json")
        store_response(key, model_id, prompt_hash(prompt), response_json)
        generation.update(output=response_json, usage_details=structured.usage_details)

    return structured.parsed
