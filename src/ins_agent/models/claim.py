"""Claim submission models: Intake Input, Submitted Documents, and the
persisted Claim shape (see `db/schema.sql`).

`PolicySearchQuery` and `IntakeInput` are kept distinct from `Claim`: the
identifying fields used for Policy Resolution (`policy_id`, `holder_name`,
`phone`, `dob`) are never persisted on the Claim itself, since they describe
the Policy Holder being searched for, not the Claimant. See CONTEXT.md for
the Claimant/Policy Holder distinction.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class DocType(StrEnum):
    POLICE_REPORT = "police_report"
    PHOTOS = "photos"
    REPAIR_ESTIMATE = "repair_estimate"
    MEDICAL_RECORDS = "medical_records"
    PROOF_OF_OWNERSHIP = "proof_of_ownership"
    IDENTIFICATION = "identification"


class Document(BaseModel):
    """Structured metadata only — never fake file content. See ADR-0004."""

    doc_type: DocType
    filename: str
    present: bool


class PolicySearchQuery(BaseModel):
    """The fields Recall uses to look up a Policy.

    In this ticket's walking skeleton these come straight off the Intake
    Input; ticket 05 replaces that with an LLM call that produces this same
    shape from messier input, so the fields must not change to accommodate
    that split.
    """

    policy_id: str | None = None
    holder_name: str | None = None
    phone: str | None = None
    dob: date | None = None


class IntakeInput(BaseModel):
    """The raw claim submission, as captured at intake."""

    policy_id: str | None = None
    holder_name: str | None = None
    phone: str | None = None
    dob: date | None = None

    claimant_name: str
    claimant_phone: str | None = None

    incident_date: date
    description: str
    requested_amount: Decimal
    documents: list[Document] = Field(default_factory=list)

    def search_query(self) -> PolicySearchQuery:
        return PolicySearchQuery(
            policy_id=self.policy_id,
            holder_name=self.holder_name,
            phone=self.phone,
            dob=self.dob,
        )


class Claim(BaseModel):
    """The persisted shape of a Claim (`claim` table)."""

    claim_id: str
    policy_id_provided: str | None
    claimant_name: str
    claimant_phone: str | None
    incident_date: date
    description: str
    requested_amount: Decimal
    documents: list[Document] = Field(default_factory=list)

    @classmethod
    def from_intake(cls, claim_id: str, intake: IntakeInput) -> "Claim":
        return cls(
            claim_id=claim_id,
            policy_id_provided=intake.policy_id,
            claimant_name=intake.claimant_name,
            claimant_phone=intake.claimant_phone,
            incident_date=intake.incident_date,
            description=intake.description,
            requested_amount=intake.requested_amount,
            documents=intake.documents,
        )
