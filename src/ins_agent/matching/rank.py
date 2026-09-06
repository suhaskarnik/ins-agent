"""Rank: deterministic weighted scoring of a candidate Policy against a
Policy Search Query.

Weights (sum to 1.0): `policy_id` exact 0.5, name up to 0.3 (Jaro-Winkler
similarity scaled, plus a Metaphone exact-match bonus when the spelling
differs but the phonetics agree), phone up to 0.15 (exact-only, after
canonicalization), DOB exact 0.05.

A Perfect Score (1.0) is Policy ID + name both exact — defined as maximal
regardless of what phone/DOB contribute, since an exact Policy ID already
identifies a unique row and the exact name confirms it; no other candidate
could plausibly also earn it. See CONTEXT.md.
"""

import re

import jellyfish

from ins_agent.models.claim import PolicySearchQuery
from ins_agent.models.policy import Policy
from ins_agent.models.triage import RankedCandidate

POLICY_ID_WEIGHT = 0.5
NAME_WEIGHT = 0.3
PHONE_WEIGHT = 0.15
DOB_WEIGHT = 0.05
NAME_PHONETIC_BONUS = 0.05


def canonicalize_phone(phone: str) -> str:
    """Digits only, with a leading US country code ('1') dropped."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def name_score(query_name: str, candidate_name: str) -> tuple[float, bool]:
    """Returns (weighted score up to NAME_WEIGHT, exact_match)."""
    a, b = _normalize_name(query_name), _normalize_name(candidate_name)
    if a == b:
        return NAME_WEIGHT, True

    similarity = jellyfish.jaro_winkler_similarity(a, b)
    score = similarity * NAME_WEIGHT
    if jellyfish.metaphone(a) == jellyfish.metaphone(b):
        score += NAME_PHONETIC_BONUS
    return min(score, NAME_WEIGHT), False


def rank_score(policy: Policy, query: PolicySearchQuery) -> RankedCandidate:
    policy_id_exact = bool(query.policy_id) and query.policy_id == policy.policy_id
    policy_id_component = POLICY_ID_WEIGHT if policy_id_exact else 0.0

    if query.holder_name:
        name_component, name_exact = name_score(query.holder_name, policy.holder_name)
    else:
        name_component, name_exact = 0.0, False

    phone_exact = query.phone is not None and canonicalize_phone(query.phone) == canonicalize_phone(
        policy.phone
    )
    phone_component = PHONE_WEIGHT if phone_exact else 0.0

    dob_exact = query.dob is not None and query.dob == policy.dob
    dob_component = DOB_WEIGHT if dob_exact else 0.0

    total = policy_id_component + name_component + phone_component + dob_component

    candidate = RankedCandidate(
        policy=policy,
        score=total,
        policy_id_exact=policy_id_exact,
        name_exact=name_exact,
        phone_exact=phone_exact,
        dob_exact=dob_exact,
    )
    # `RankedCandidate.is_perfect` is the single source of truth for what
    # counts as a Perfect Score — re-derive the score from it rather than
    # re-checking `policy_id_exact and name_exact` here too, so the two
    # can't drift apart.
    if candidate.is_perfect:
        candidate = candidate.model_copy(update={"score": 1.0})
    return candidate
