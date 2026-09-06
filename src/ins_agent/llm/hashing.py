"""Content-addressed cache key derivation for `cached_invoke`."""

import hashlib


def prompt_hash(rendered_prompt: str) -> str:
    return hashlib.sha256(rendered_prompt.encode("utf-8")).hexdigest()


def cache_key(model_id: str, rendered_prompt: str, output_schema_name: str) -> str:
    payload = f"{model_id}{rendered_prompt}{output_schema_name}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
