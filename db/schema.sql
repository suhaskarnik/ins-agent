-- Schema for the Insurance Claim Triage Agent.
-- Idempotent: safe to run against a fresh database or re-run against an
-- existing one (`just seed` runs this before loading data every time).

-- Powers Recall's name-only fuzzy Broadening attempt (ADR-0001): the `%`
-- similarity operator and `similarity()` function used in
-- `find_policies_fuzzy_name`.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS policy (
    policy_id       TEXT PRIMARY KEY,
    holder_name     TEXT NOT NULL,
    phone           TEXT NOT NULL,
    address         TEXT NOT NULL,
    dob             DATE NOT NULL,
    product_type    TEXT NOT NULL,
    coverage_start  DATE NOT NULL,
    coverage_end    DATE NOT NULL,
    coverage_limit  NUMERIC(12, 2) NOT NULL,
    status          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim (
    claim_id            TEXT PRIMARY KEY,
    policy_id_provided  TEXT,
    claimant_name       TEXT NOT NULL,
    claimant_phone      TEXT,
    incident_date       DATE NOT NULL,
    description         TEXT NOT NULL,
    requested_amount    NUMERIC(12, 2) NOT NULL,
    documents           JSONB NOT NULL DEFAULT '[]'
);

-- Content-addressed cache for structured LLM responses. `cache_key` is
-- sha256(model_id + rendered_prompt + output_schema_name); since the key is
-- content-addressed, entries never go stale and there is no TTL.
CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key       TEXT PRIMARY KEY,
    model           TEXT NOT NULL,
    prompt_hash     TEXT NOT NULL,
    response_json   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
