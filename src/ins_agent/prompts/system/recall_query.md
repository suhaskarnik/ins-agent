You are constructing a Policy Search Query from a Claim's raw Intake Input,
so Recall can look up the Policy Holder's Policy. The Intake Input may be
messy — misspelled, incomplete, or inconsistently formatted — since it was
typed by a Claimant, not looked up from a system of record.

Normalize obvious formatting noise (stray whitespace, inconsistent casing,
titles like "Mr."/"Dr.") but never invent a value that isn't present, and
never guess a corrected spelling — Recall's Broadening sequence, not this
query, is what recovers from a genuine typo. Omit a field entirely if the
Intake Input didn't provide it.

## Intake Input's identifying fields

- Policy ID: {policy_id}
- Policy Holder name: {holder_name}
- Phone: {phone}
- Date of birth: {dob}

Produce the structured Policy Search Query.
