"""
Note history — auto-saves every generated note keyed by patient ID + timestamp.
Stored in %APPDATA%/DentalScribe/history.json (unencrypted JSON, no raw PHI
beyond what the user already chose to keep locally).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_HISTORY_FILE = (
    Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe" / "history.json"
)
_MAX_ENTRIES = 500


def _load_raw() -> list[dict]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        with _HISTORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_raw(entries: list[dict]) -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def save_entry(patient_id: str, template: str, transcript: str, note: str) -> None:
    entries = _load_raw()
    entries.insert(0, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patient_id": patient_id or "",
        "template": template or "",
        "transcript": transcript or "",
        "note": note or "",
    })
    _save_raw(entries[:_MAX_ENTRIES])


def load_entries(patient_id: str = "") -> list[dict]:
    """Return entries, optionally filtered by patient_id."""
    entries = _load_raw()
    if patient_id:
        entries = [e for e in entries if e.get("patient_id") == patient_id]
    return entries


def delete_entry(timestamp: str) -> None:
    entries = [e for e in _load_raw() if e.get("timestamp") != timestamp]
    _save_raw(entries)
