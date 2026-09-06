# Auto Claim Eligibility Guideline

This document is owned by the claims triage agent's own configuration. It is
never supplied or editable by a Claimant, and is the sole basis for the
Eligibility Judgment and the Sufficiency Assessment's required-document set.

## Eligibility criteria

A claim is eligible when, in addition to passing the deterministic Coverage
Check (requested amount within the coverage limit, incident date within the
coverage window), all of the following qualitative criteria hold:

- The policy `status` is `active` at the time of the incident. A `cancelled`
  or `expired` policy is never eligible, regardless of dates on paper.
- The incident `description` is consistent with the policy's `product_type`
  (e.g. a collision claim against an "Auto - Liability" policy, which does
  not cover the claimant's own vehicle damage, should be flagged
  ineligible).
- The `requested_amount` is plausible given the incident described — a
  request wildly disproportionate to a minor described incident should be
  flagged as a concern, though not automatically ineligible; use judgment
  and explain your reasoning.

## Required documents by product type

- **Auto - Liability**: `police_report`, `photos`.
- **Auto - Collision**: `police_report`, `photos`, `repair_estimate`.
- **Auto - Comprehensive**: `photos`, `repair_estimate`.
- **Auto - Full Coverage**: `police_report`, `photos`, `repair_estimate`.

A claim involving any injury (per the incident description) additionally
requires `medical_records`. `identification` and `proof_of_ownership` are
never required by default but strengthen a submission when present.

A submission is sufficient only when every document required for the
policy's `product_type` (and, where applicable, an injury) is both present
in the Submitted Documents and marked `present: true`.
