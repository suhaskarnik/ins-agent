-- Schema for the Insurance Claim Triage Agent.
-- Idempotent: safe to run against a fresh database or re-run against an
-- existing one (`just seed` runs this before loading data every time).

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
