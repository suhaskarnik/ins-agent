from datetime import date
from decimal import Decimal

import pytest

from ins_agent.matching.rank import canonicalize_phone, rank_score
from ins_agent.models.claim import PolicySearchQuery
from ins_agent.models.policy import Policy

POLICY = Policy(
    policy_id="POL-00002",
    holder_name="Brent Abbott",
    phone="940-781-6184",
    address="310 Kendra Common Apt. 164, Reidstad, GA 49021",
    dob=date(1964, 11, 2),
    product_type="Auto - Comprehensive",
    coverage_start=date(2025, 8, 4),
    coverage_end=date(2026, 4, 17),
    coverage_limit=Decimal("50000"),
    status="active",
)


def test_canonicalize_phone_strips_formatting():
    assert canonicalize_phone("940-781-6184") == "9407816184"
    assert canonicalize_phone("(940) 781-6184") == "9407816184"


def test_canonicalize_phone_drops_leading_us_country_code():
    assert canonicalize_phone("1-940-781-6184") == "9407816184"


def test_exact_policy_id_and_name_is_a_perfect_score():
    query = PolicySearchQuery(policy_id="POL-00002", holder_name="Brent Abbott")
    result = rank_score(POLICY, query)
    assert result.score == 1.0
    assert result.is_perfect


def test_perfect_score_holds_even_with_no_phone_or_dob_provided():
    query = PolicySearchQuery(policy_id="POL-00002", holder_name="Brent Abbott")
    result = rank_score(POLICY, query)
    assert result.score == 1.0


def test_wrong_policy_id_is_not_a_perfect_score():
    query = PolicySearchQuery(policy_id="POL-99999", holder_name="Brent Abbott")
    result = rank_score(POLICY, query)
    assert not result.is_perfect
    assert result.score < 1.0


def test_name_only_typo_scores_below_perfect_but_above_zero():
    query = PolicySearchQuery(holder_name="Brendt Abbot")
    result = rank_score(POLICY, query)
    assert 0.0 < result.score < 0.3
    assert not result.name_exact


def test_phonetically_similar_but_misspelled_name_gets_a_bonus():
    # "Abott" is one edit from "Abbott" (high Jaro-Winkler) and shares its
    # Metaphone code, so the bonus can push it up to the name weight's cap
    # even though it isn't a spelling-exact match.
    typo_query = PolicySearchQuery(holder_name="Brent Abott")
    result = rank_score(POLICY, typo_query)

    assert result.score == pytest.approx(0.3)
    assert not result.name_exact
    assert not result.is_perfect

    # A genuinely dissimilar name (different Metaphone, low Jaro-Winkler)
    # gets no bonus and scores well below the cap.
    dissimilar_query = PolicySearchQuery(holder_name="Jordan Fischer")
    dissimilar_result = rank_score(POLICY, dissimilar_query)
    assert dissimilar_result.score < 0.15


def test_no_query_fields_scores_zero():
    result = rank_score(POLICY, PolicySearchQuery())
    assert result.score == 0.0
    assert not result.is_perfect
