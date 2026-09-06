"""Writes an approved Notification to disk, standing in for an actual send.
See CONTEXT.md — no message is ever actually sent from this POC."""

from datetime import UTC, datetime
from pathlib import Path

from ins_agent.models.triage import Notification
from ins_agent.paths import REPO_ROOT

OUTPUT_DIR = REPO_ROOT / "data" / "output"


def write_notification(claim_id: str, notification: Notification) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = OUTPUT_DIR / f"{claim_id}_{timestamp}.txt"
    path.write_text(f"Subject: {notification.subject}\n\n{notification.body}\n")
    return path
