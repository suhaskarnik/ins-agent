"""Interactive field-by-field Intake Input prompt for `just run`.

Simulates an ad-hoc, possibly incomplete claim form submission — optional
fields can be skipped by pressing enter.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ins_agent.models.claim import DocType, Document, IntakeInput


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


def _prompt_yes_no(label: str, *, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{label} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def _prompt_doc_type() -> DocType | None:
    doc_types = list(DocType)
    options = ", ".join(doc_type.value for doc_type in doc_types)
    while True:
        raw = input(f"  Document type ({options}, or enter to finish): ").strip().lower()
        if not raw:
            return None
        for doc_type in doc_types:
            if doc_type.value == raw:
                return doc_type
        print(f"Please enter one of: {options}")


def prompt_documents() -> list[Document]:
    print("Attach documents (enter a document type to add one, blank to finish):")
    documents: list[Document] = []
    while True:
        doc_type = _prompt_doc_type()
        if doc_type is None:
            return documents
        filename = _prompt_required("  Filename")
        is_present = _prompt_yes_no("  Is the document actually attached", default=True)
        documents.append(Document(doc_type=doc_type, filename=filename, present=is_present))


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
    documents = prompt_documents()

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
        documents=documents,
    )
