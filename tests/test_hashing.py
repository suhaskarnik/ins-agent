from ins_agent.llm.hashing import cache_key, prompt_hash


def test_cache_key_is_deterministic():
    first = cache_key("groq:llama-3.1-8b-instant", "find the policy", "PolicySearchQuery")
    second = cache_key("groq:llama-3.1-8b-instant", "find the policy", "PolicySearchQuery")
    assert first == second


def test_cache_key_changes_with_model():
    a = cache_key("model-a", "same prompt", "Schema")
    b = cache_key("model-b", "same prompt", "Schema")
    assert a != b


def test_cache_key_changes_with_prompt():
    a = cache_key("model", "prompt one", "Schema")
    b = cache_key("model", "prompt two", "Schema")
    assert a != b


def test_cache_key_changes_with_schema_name():
    a = cache_key("model", "prompt", "SchemaA")
    b = cache_key("model", "prompt", "SchemaB")
    assert a != b


def test_cache_key_does_not_collide_across_field_boundary():
    a = cache_key("ChatGroq:m1", "2 is the answer", "Foo")
    b = cache_key("ChatGroq:m", "12 is the answer", "Foo")
    assert a != b


def test_prompt_hash_is_deterministic():
    assert prompt_hash("hello") == prompt_hash("hello")
    assert prompt_hash("hello") != prompt_hash("world")
