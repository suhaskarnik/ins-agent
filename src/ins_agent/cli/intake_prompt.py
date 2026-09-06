"""Interactive field-by-field Intake Input prompt for `just run`.

Simulates an ad-hoc, possibly incomplete claim form submission — optional
fields can be skipped by pressing enter.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ins_agent.models.claim import IntakeInput


def _prompt_optional(label: str) -> str | None:
    value = input(f"{label} (optional, enter to skip): ").strip()
    return value or None


def _prompt_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(f"{label} is required.")


def _prompt_optional_date(label: str) -> date | None:
    while True:
        raw = _prompt_optional(f"{label} (YYYY-MM-DD)")
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Please enter a date as YYYY-MM-DD, or leave blank to skip.")


def _prompt_required_date(label: str) -> date:
    while True:
        raw = _prompt_required(f"{label} (YYYY-MM-DD)")
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Please enter a date as YYYY-MM-DD.")


def _prompt_amount(label: str) -> Decimal:
    while True:
        raw = _prompt_required(label)
        try:
            return Decimal(raw)
        except InvalidOperation:
            print("Please enter a plain number, e.g. 3200.00.")


def prompt_intake_input() -> IntakeInput:
    print("--- Claim intake ---")
    print("Policy Holder identifying details (used to look up the Policy):")
    policy_id = _prompt_optional("  Policy ID")
    holder_name = _prompt_optional("  Policy Holder name")
    phone = _prompt_optional("  Policy Holder phone")
    dob = _prompt_optional_date("  Policy Holder date of birth")

    print("Claimant details:")
    claimant_name = _prompt_required("  Claimant name")
    claimant_phone = _prompt_optional("  Claimant phone")

    print("Claim details:")
    incident_date = _prompt_required_date("  Incident date")
    description = _prompt_required("  Description")
    requested_amount = _prompt_amount("  Requested amount")

    return IntakeInput(
        policy_id=policy_id,
        holder_name=holder_name,
        phone=phone,
        dob=dob,
        claimant_name=claimant_name,
        claimant_phone=claimant_phone,
        incident_date=incident_date,
        description=description,
        requested_amount=requested_amount,
        documents=[],
    )
