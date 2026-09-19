# Insurance Claim Triage Agent

A LangGraph agent that triages an insurance claim submission end-to-end — resolving it against a policy database, checking eligibility, assessing documentation, and preparing a recommendation — then stops in front of a human before anything customer-facing goes out.

It's a proof of concept built to demonstrate a specific architectural stance: **push every decision that can be made deterministically out of the LLM's hands, reserve the LLM for the judgment calls that genuinely need it, and never let the two get presented to a human as if they carry the same weight.**

Fake data throughout (a seeded Postgres database of ~40 policies, six scripted claim scenarios) — no real insurer, no real PII, no real emails sent.

## Why this exists

Most agent demos either do everything with an LLM (unreliable, unauditable) or do everything with rules (brittle, can't handle messy input). This project picks apart one realistic workflow — claim triage — and deliberately routes each step to whichever approach actually fits it:

| Step | Approach | Why |
|---|---|---|
| Find candidate policies from messy input | LLM | Input can be incomplete, misspelled, or wrong — needs judgment to construct a search |
| Score how well each candidate matches | Deterministic (Jaro-Winkler, Metaphone, phone canonicalization) | A match score should be reproducible and explainable, not vibes |
| Retry a failed search | Deterministic, fixed sequence | The retry path should never surprise anyone — see [ADR-0001](docs/adr/0001-deterministic-broadening.md) |
| Pick between ambiguous candidates | Human | Nobody should let an LLM guess which of two people filed a claim |
| Check coverage limits / dates | Deterministic | It's arithmetic, not judgment |
| Assess eligibility against guidelines | LLM | Genuinely requires reading unstructured criteria and reasoning about fit — kept separate from the arithmetic, never blended: [ADR-0002](docs/adr/0002-eligibility-split.md) |
| Assess document sufficiency | LLM | Judging whether a *set* of documents satisfies a requirement is a reasoning task |
| Approve the outcome and send anything | Human | Always. No payment or communication reaches a customer without a human gate |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full pipeline diagram, data model, and the reasoning behind each notable decision. The original requirements this project was built from are preserved in [SPEC.md](SPEC.md).

The domain vocabulary (Policy vs. Claimant vs. Policy Holder, Recall vs. Rank, Coverage Check vs. Eligibility Judgment, etc.) is defined in [CONTEXT.md](CONTEXT.md) — worth a skim before reading the code, since the code uses these terms precisely.

## Stack

- **LangGraph** — the triage pipeline, including two durable human-in-the-loop interrupts backed by a Postgres checkpointer
- **LangChain** — model access, structured output enforcement (`with_structured_output` everywhere an LLM produces a step's result)
- **Groq**, swappable to OpenRouter via one `.env` variable, with model selection abstracted behind two tiers (`model_fast` / `model_reasoning`) rather than hardcoded model names
- **Postgres** (local, via `podman-compose`) — policy/claim data, the LangGraph checkpointer, and a content-addressed LLM response cache
- **Langfuse** (your own instance, via `.env`) — every LLM call traced, including cache hits
- **Pydantic** / **pydantic-settings** — structured data at every boundary, including config
- **uv** for package management, **just** for task automation

## Quickstart

```bash
just up             # start local Postgres via podman-compose
just seed           # load fake policy data
just run-scenario tc001   # run one scripted scenario through the full pipeline
```

Or `just run` for an interactive TUI that prompts for claim details the way a real intake form would.

Six scenarios ship in `data/tests/` (`tc001`–`tc006`), each exercising a different branch of the graph — clean match, fuzzy match, ambiguous match requiring human selection, no match found, ineligible claim, insufficient documentation. `just test` runs all of them as a regression suite.

Every drafted customer notification is written to `data/output/` as plain text instead of actually being sent — see [CONTEXT.md](CONTEXT.md#final-review) for why.

## Status

All six scenarios (tc001–tc006), the eval-drift suite, and Langfuse tracing are implemented. See [docs/demo.md](docs/demo.md) for a recorded walkthrough, real traces, and eval output.

## License

MIT
