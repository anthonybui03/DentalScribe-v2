"""
Local Whisper transcription.
Supports two backends:
  1. faster-whisper  (preferred — GPU/CPU, very fast)
  2. openai-whisper  (fallback, pure Python)
Both run 100% locally. No data leaves the machine.
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Literal

# The chosen backend is set in config; default to faster-whisper.
Backend = Literal["faster-whisper", "openai-whisper"]

_model_cache: dict = {}


def _load_faster_whisper(model_size: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel
    key = ("faster-whisper", model_size, device)
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _model_cache[key]


def _load_openai_whisper(model_size: str):
    import whisper
    key = ("openai-whisper", model_size)
    if key not in _model_cache:
        _model_cache[key] = whisper.load_model(model_size)
    return _model_cache[key]


def transcribe(
    wav_bytes: bytes,
    backend: Backend = "faster-whisper",
    model_size: str = "base.en",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "en",
) -> str:
    """
    Transcribe WAV audio bytes to text using the specified local Whisper backend.
    Returns the transcript string.
    """
    if not wav_bytes:
        return ""

    # Write to a temp file because both libraries expect a file path.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    try:
        if backend == "faster-whisper":
            model = _load_faster_whisper(model_size, device, compute_type)
            segments, _ = model.transcribe(tmp_path, language=language, beam_size=5)
            return " ".join(seg.text.strip() for seg in segments)
        else:
            import whisper
            model = _load_openai_whisper(model_size)
            result = model.transcribe(tmp_path, language=language)
            return result["text"].strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def list_available_models() -> list[str]:
    return ["tiny.en", "base.en", "small.en", "medium.en", "large-v3"]
