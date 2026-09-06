# Eligibility is reported as two distinct fields, never blended

Eligibility could be a single LLM call that reasons over both coverage math (amount vs. limit, incident date vs. coverage window) and qualitative fit against the Guideline, returning one verdict. We split it instead: a deterministic Coverage Check and a separate LLM Eligibility Judgment, reported as two fields.

A blended verdict would read to the reviewer as one fact, but part of it would actually be arithmetic (trustworthy, checkable) and part would be model judgment (not). This project's whole premise is that deterministic and non-deterministic outputs must never be presented as though they're at the same level of veracity — Eligibility is the clearest place that principle could quietly get violated, so it's enforced structurally here rather than left to prompt wording.
