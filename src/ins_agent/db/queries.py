"""Policy queries.

`find_policies_exact` deterministically maps a `PolicySearchQuery` to a
parameterized SQL `WHERE` clause — no query field (whether typed directly,
as in this ticket, or produced by an LLM, as in ticket 05) ever reaches the
database as raw SQL or plaintext.
"""

from ins_agent.config import get_settings
from ins_agent.db.connection import get_connection
from ins_agent.models.claim import PolicySearchQuery
from ins_agent.models.policy import Policy

_COLUMNS = [
    "policy_id",
    "holder_name",
    "phone",
    "address",
    "dob",
    "product_type",
    "coverage_start",
    "coverage_end",
    "coverage_limit",
    "status",
]


def find_policies_exact(query: PolicySearchQuery) -> list[Policy]:
    """Every provided field must match exactly (AND). A query with no
    fields set matches nothing — Recall never returns the whole table."""
    clauses = []
    params: list[str] = []

    if query.policy_id:
        clauses.append("policy_id = %s")
        params.append(query.policy_id)
    if query.holder_name:
        clauses.append("holder_name = %s")
        params.append(query.holder_name)
    if query.phone:
        clauses.append("phone = %s")
        params.append(query.phone)
    if query.dob:
        clauses.append("dob = %s")
        params.append(query.dob.isoformat())

    if not clauses:
        return []

    sql = f"SELECT {', '.join(_COLUMNS)} FROM policy WHERE {' AND '.join(clauses)}"

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [Policy(**dict(zip(_COLUMNS, row, strict=True))) for row in rows]


def find_policies_fuzzy_name(
    name: str, policy_id: str | None = None, limit: int | None = None
) -> list[Policy]:
    """Recall's final Broadening attempt (see ADR-0001) — trigram similarity
    via `pg_trgm`'s `%` operator, not exact equality, so a misspelled name
    still surfaces the right Policy as a candidate for Rank to score.

    `limit` defaults to the same `top_n` Policy Resolution tuning knob the
    rest of Recall/Rank respects, rather than a second hardcoded cap. When a
    `policy_id` is also known (it just failed the earlier exact-match
    attempts because the name didn't match literally), it's OR'd into the
    `WHERE` clause and ranked first — otherwise a `LIMIT`-truncated result
    could drop the one candidate whose policy_id already proves it's the
    right Policy, in favor of others that merely look more like the typo'd
    name.
    """
    limit = limit if limit is not None else get_settings().top_n

    if policy_id:
        sql = (
            f"SELECT {', '.join(_COLUMNS)} FROM policy "
            "WHERE holder_name %% %s OR policy_id = %s "
            "ORDER BY (policy_id = %s) DESC, similarity(holder_name, %s) DESC LIMIT %s"
        )
        params: list[str | int] = [name, policy_id, policy_id, name, limit]
    else:
        sql = (
            f"SELECT {', '.join(_COLUMNS)} FROM policy "
            "WHERE holder_name %% %s ORDER BY similarity(holder_name, %s) DESC LIMIT %s"
        )
        params = [name, name, limit]

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [Policy(**dict(zip(_COLUMNS, row, strict=True))) for row in rows]
