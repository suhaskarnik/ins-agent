"""The Policy record, as stored in `policy` (see `db/schema.sql`)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Policy(BaseModel):
    policy_id: str
    holder_name: str
    phone: str
    address: str
    dob: date
    product_type: str
    coverage_start: date
    coverage_end: date
    coverage_limit: Decimal
    status: str
