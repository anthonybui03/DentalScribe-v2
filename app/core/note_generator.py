"""
Dental note generation via a local Ollama LLM.
Calls http://localhost:11434 (or a configurable host) — never reaches the internet.
"""
import json
import urllib.request
import urllib.error
from typing import Generator

SYSTEM_PROMPT = (
    "You are a dental documentation assistant for a pediatric dental office. "
    "Convert dictated clinical text into a professional dental chart note. "
    "Do not invent facts. Do not add diagnoses, treatment, medications, tooth numbers, "
    "or procedures unless they were clearly stated. If information is missing, write "
    "'not stated.' Keep the note concise, clinically appropriate, and ready for provider "
    "review. The provider must verify before chart entry."
)

WARNING_FOOTER = (
    "\n\n---\n⚠️  PROVIDER REVIEW REQUIRED — This note was AI-generated and must be "
    "verified by the treating provider before being added to the patient chart."
)


def generate_note(
    transcript: str,
    template_instruction: str = "",
    ollama_host: str = "http://localhost:11434",
    model: str = "llama3",
    stream: bool = False,
) -> str | Generator[str, None, None]:
    """
    Send the transcript to Ollama and return the generated dental note.
    If stream=True, yields text chunks as they arrive.
    """
    user_content = transcript.strip()
    if template_instruction:
        user_content = f"{template_instruction}\n\nDictation:\n{user_content}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": stream,
        "options": {
            "temperature": 0.2,   # Low temp = more conservative, less hallucination
            "num_predict": 1024,
        },
    }

    url = f"{ollama_host.rstrip('/')}/api/chat"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    if stream:
        return _stream_response(req)
    else:
        return _blocking_response(req)


def _blocking_response(req: urllib.request.Request) -> str:
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            lines = resp.read().decode("utf-8").strip().split("\n")
            parts = []
            for line in lines:
                try:
                    obj = json.loads(line)
                    content = obj.get("message", {}).get("content", "")
                    if content:
                        parts.append(content)
                except json.JSONDecodeError:
                    pass
            return "".join(parts) + WARNING_FOOTER
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Cannot reach Ollama at {req.full_url}. "
            "Is Ollama running? Run: ollama serve"
        ) from e


def _stream_response(req: urllib.request.Request) -> Generator[str, None, None]:
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    content = obj.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if obj.get("done"):
                        yield WARNING_FOOTER
                        break
                except json.JSONDecodeError:
                    pass
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Cannot reach Ollama. Is it running? (ollama serve)"
        ) from e


def list_ollama_models(ollama_host: str = "http://localhost:11434") -> list[str]:
    """Return model names available in the local Ollama instance."""
    url = f"{ollama_host.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def check_ollama_health(ollama_host: str = "http://localhost:11434") -> bool:
    try:
        with urllib.request.urlopen(f"{ollama_host.rstrip('/')}/api/tags", timeout=3):
            return True
    except Exception:
        return False
