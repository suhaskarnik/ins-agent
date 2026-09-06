"""Policy queries.

`find_policies_exact` deterministically maps a `PolicySearchQuery` to a
parameterized SQL `WHERE` clause — no query field (whether typed directly,
as in this ticket, or produced by an LLM, as in ticket 05) ever reaches the
database as raw SQL or plaintext.
"""

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
