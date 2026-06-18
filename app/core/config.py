"""App configuration — stored in %APPDATA%/DentalScribe-v2/config.json"""
import json
import os
from pathlib import Path

_CONFIG_DIR  = Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe-v2"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "whisper_backend":            "faster-whisper",
    "whisper_model":              "base.en",
    "whisper_device":             "cpu",
    "whisper_compute_type":       "float32",
    "ollama_host":                "http://localhost:11434",
    "ollama_model":               "llama3",
    "mic_device_index":           None,
    "pin_hash":                   "",
    "inactivity_timeout_minutes": 10,
    "save_notes_locally":         True,
    "save_raw_audio":             False,
    "encrypt_at_rest":            True,
    "od_api_url":                 "",
    "od_developer_key":           "",
    "od_customer_key":            "",
    "default_template":           "Custom / Freeform",
    "onboarding_complete":        False,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    if _CONFIG_FILE.exists():
        try:
            with _CONFIG_FILE.open("r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print(f"[config] {e}")
    return cfg


def save(cfg: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in cfg.items() if not k.startswith("_")}
    with _CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2)


def notes_dir() -> Path:
    d = _CONFIG_DIR / "notes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def audio_dir() -> Path:
    d = _CONFIG_DIR / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d
