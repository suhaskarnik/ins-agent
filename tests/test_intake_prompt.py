"""Unit tests for the interactive `just run` Intake Input prompt (ticket 11).

`input()` is monkeypatched to replay a canned sequence of answers, so these
exercise the parsing/validation logic without a real terminal.
"""

from datetime import date
from decimal import Decimal

import pytest

from ins_agent.cli.intake_prompt import prompt_documents, prompt_intake_input
from ins_agent.models.claim import DocType, Document


def _fake_input(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    responses = iter(answers)

    def _next(_prompt: str = "") -> str:
        return next(responses)

    monkeypatch.setattr("builtins.input", _next)


def test_prompt_documents_stops_on_blank_line(monkeypatch: pytest.MonkeyPatch):
    _fake_input(monkeypatch, [""])
    assert prompt_documents() == []


def test_prompt_documents_collects_one_document(monkeypatch: pytest.MonkeyPatch):
    _fake_input(monkeypatch, ["photos", "damage.jpg", "y", ""])
    assert prompt_documents() == [
        Document(doc_type=DocType.PHOTOS, filename="damage.jpg", present=True)
    ]


def test_prompt_documents_collects_multiple_and_supports_not_present(
    monkeypatch: pytest.MonkeyPatch,
):
    _fake_input(
        monkeypatch,
        [
            "photos",
            "damage.jpg",
            "y",
            "police_report",
            "report.pdf",
            "n",
            "",
        ],
    )
    assert prompt_documents() == [
        Document(doc_type=DocType.PHOTOS, filename="damage.jpg", present=True),
        Document(doc_type=DocType.POLICE_REPORT, filename="report.pdf", present=False),
    ]


def test_prompt_documents_reprompts_on_invalid_doc_type(monkeypatch: pytest.MonkeyPatch):
    _fake_input(monkeypatch, ["not-a-type", "photos", "damage.jpg", "y", ""])
    assert prompt_documents() == [
        Document(doc_type=DocType.PHOTOS, filename="damage.jpg", present=True)
    ]


def test_prompt_intake_input_collects_full_claim_with_documents(
    monkeypatch: pytest.MonkeyPatch,
):
    _fake_input(
        monkeypatch,
        [
            "POL-00002",  # policy_id
            "Brent Abbott",  # holder_name
            "940-781-6184",  # phone
            "1964-11-02",  # dob
            "Brent Abbott",  # claimant_name
            "940-781-6184",  # claimant_phone
            "2025-09-10",  # incident_date
            "Rear windshield cracked by a fallen tree branch",  # description
            "3200.00",  # requested_amount
            "photos",
            "damage_photo_1.jpg",
            "y",
            "",  # done adding documents
        ],
    )

    intake = prompt_intake_input()

    assert intake.policy_id == "POL-00002"
    assert intake.holder_name == "Brent Abbott"
    assert intake.dob == date(1964, 11, 2)
    assert intake.incident_date == date(2025, 9, 10)
    assert intake.requested_amount == Decimal("3200.00")
    assert intake.documents == [
        Document(doc_type=DocType.PHOTOS, filename="damage_photo_1.jpg", present=True)
    ]


def test_prompt_intake_input_allows_skipping_optional_fields(monkeypatch: pytest.MonkeyPatch):
    _fake_input(
        monkeypatch,
        [
            "",  # policy_id skipped
            "",  # holder_name skipped
            "",  # phone skipped
            "",  # dob skipped
            "Jordan Ellison",  # claimant_name (required)
            "",  # claimant_phone skipped
            "2025-06-15",  # incident_date
            "Side mirror snapped off",  # description
            "800.00",  # requested_amount
            "",  # no documents
        ],
    )

    intake = prompt_intake_input()

    assert intake.policy_id is None
    assert intake.holder_name is None
    assert intake.phone is None
    assert intake.dob is None
    assert intake.claimant_phone is None
    assert intake.documents == []
