"""
Append-only encrypted audit log stored locally.
Each entry is a JSON line encrypted with Fernet and base64-encoded.
The log file lives in %APPDATA%/DentalScribe/audit/ (Windows).
"""
import getpass
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

_LOG_DIR = Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe" / "audit"
_LOG_FILE = _LOG_DIR / "audit.log"


def _log_dir() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def _windows_username() -> str:
    try:
        return os.getlogin()
    except Exception:
        return getpass.getuser()


def append_entry(
    action: str,
    fernet: Fernet,
    patient_id: str = "",
    note_text: str = "",
    extra: dict | None = None,
) -> None:
    """Write one encrypted audit entry to the log."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": _windows_username(),
        "action": action,
        "patient_id": patient_id,
        "hostname": platform.node(),
        "note_preview": note_text[:200] if note_text else "",
    }
    if extra:
        entry.update(extra)

    raw = json.dumps(entry, ensure_ascii=False)
    encrypted_line = fernet.encrypt(raw.encode("utf-8")).decode("ascii")

    log_file = _log_dir() / "audit.log"
    with log_file.open("a", encoding="ascii") as f:
        f.write(encrypted_line + "\n")


def read_entries(fernet: Fernet, max_entries: int = 500) -> list[dict]:
    """Decrypt and return the most recent audit entries."""
    log_file = _log_dir() / "audit.log"
    if not log_file.exists():
        return []

    lines = log_file.read_text(encoding="ascii").splitlines()
    # Read newest first, up to max_entries.
    results = []
    for line in reversed(lines[-max_entries:]):
        line = line.strip()
        if not line:
            continue
        try:
            raw = fernet.decrypt(line.encode("ascii")).decode("utf-8")
            results.append(json.loads(raw))
        except (InvalidToken, Exception):
            results.append({"ts": "?", "action": "[unreadable entry]", "user": "?"})
    return results


def export_log_plaintext(fernet: Fernet, dest_path: Path) -> int:
    """Decrypt all entries and write as plain JSON-Lines to dest_path. Returns count."""
    entries = read_entries(fernet, max_entries=100_000)
    with dest_path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(entries)
