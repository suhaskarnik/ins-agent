# Insurance Claim Triage

An agent that intakes a claim submission, finds the Policy it belongs to, and prepares a triage recommendation for a human reviewer to approve. It exists to separate the parts of triage that should be deterministic from the parts that genuinely require judgment, and to make that separation visible to the reviewer rather than blending the two.

## Language

### Identity

**Policy**:
The insurance contract on file — holder identity, product, coverage window, and coverage limit.
_Avoid_: Contract, plan.

**Policy Holder**:
The person named on a Policy. Distinct from the Claimant.
_Avoid_: Insured, account holder.

**Claimant**:
The person submitting a Claim. May or may not be the Policy Holder (e.g. a family member filing on the holder's behalf) — the triage agent does not assume they're the same person, and a Claimant/Holder mismatch is a real outcome, not just noise to fuzzy-match away.
_Avoid_: Submitter, user.

**Intake Input**:
The raw identifying details submitted with a claim (policy ID, name, phone, DOB) — may be complete, incomplete, correct, or incorrect. Used to locate the Policy the Claim belongs to.
_Avoid_: Form data, request payload.

### Policy Resolution

**Recall**:
The step that searches for candidate Policies from Intake Input, optimizing for finding every plausible match even at the cost of false positives.
_Avoid_: Search, lookup.

**Rank Score**:
A deterministic, weighted score (0–1) expressing how well a candidate Policy matches the Intake Input, optimizing for precision after Recall has cast a wide net.
_Avoid_: Confidence, similarity.

**Match Threshold**:
The configurable minimum Rank Score a candidate must clear to be treated as a genuine match rather than noise.
_Avoid_: Cutoff, confidence level.

**Perfect Score**:
A Rank Score of 1.0 — Policy ID and Policy Holder name both match exactly. Resolves Policy Resolution without a human gate, since no other candidate could plausibly also earn this.
_Avoid_: Exact match.

**Broadening**:
The fixed, deterministic sequence of loosening Recall's search criteria across retry attempts (e.g. dropping DOB/phone, then falling back to name-only) when no candidate clears the Match Threshold. Follows a fixed sequence rather than LLM judgment so the retry path stays predictable and testable — see [ADR-0001](docs/adr/0001-deterministic-broadening.md).
_Avoid_: Retry, fallback search.

**Policy Selection Gate**:
The human-in-the-loop checkpoint reached when Recall/Rank produce multiple candidates near the Match Threshold with no single Perfect Score or unambiguous top choice — the human picks the correct Policy.
_Avoid_: HITL step 1, disambiguation.

### Eligibility and Documentation

**Coverage Check**:
The deterministic sub-check of Eligibility — does the requested amount fall within the Policy's coverage limit, and does the incident date fall within the coverage window.
_Avoid_: Eligibility (on its own, when the deterministic check specifically is meant).

**Eligibility Judgment**:
The LLM's qualitative assessment of whether a Claim fits the Policy's terms per the Guideline — separate from, and never blended with, the Coverage Check's deterministic result. Reported as two distinct fields so the reviewer never mistakes a judgment call for a fact — see [ADR-0002](docs/adr/0002-eligibility-split.md).
_Avoid_: Eligibility check (ambiguous between this and Coverage Check).

**Guideline**:
The Markdown document describing completeness and eligibility requirements for a claim. Owned by the agent's configuration, never supplied by the Claimant.
_Avoid_: Policy wording, rules doc.

**Submitted Documents**:
Structured metadata (document type + presence) describing what was submitted with a Claim. Never actual file content — the agent doesn't fabricate or read document bodies, only what a form-intake step would actually capture.
_Avoid_: Attachments, files.

**Sufficiency Assessment**:
The LLM's judgment of whether Submitted Documents satisfy the Guideline's required set for this Claim.
_Avoid_: Document check.

### Final Review

**Final Review Gate**:
The terminal human-in-the-loop checkpoint. The agent presents its full recommendation (Policy Resolution confidence, Coverage Check result, Eligibility Judgment, Sufficiency Assessment) plus a drafted Notification; the human approves or rejects.
_Avoid_: HITL step 2, final HITL.

**Notification**:
The customer-facing message the agent drafts for the Final Review Gate. No message is ever actually sent — an approved Notification is written to disk as text, standing in for the send.
_Avoid_: Email (no email is actually sent).

### Supporting Concepts

**Scenario**:
A named, reproducible fixture (`tc001`, `tc002`, …) pairing a specific Intake Input with seed data, used to exercise one branch of the triage graph end-to-end.
_Avoid_: Test case, fixture.

**Model Tier**:
An abstraction (`model_fast` / `model_reasoning`) that selects an LLM by the judgment complexity a task requires, independent of which provider or concrete model is behind it.
_Avoid_: Model class, model config.

**Cache Hit**:
Reuse of a prior LLM response because the current call has the same content-addressed key (model + rendered prompt + output schema) as one already answered — done to conserve token spend, always logged to the trace even when it short-circuits the real call.
_Avoid_: Memoization.
