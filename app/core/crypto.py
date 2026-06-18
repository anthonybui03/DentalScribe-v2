"""
Encryption helpers for notes, audio, and audit logs at rest.
Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
The key is derived from the app PIN via PBKDF2.
"""
import os
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Salt file lives next to the data directory; never stored with the data.
_SALT_FILE = Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe" / "salt.bin"


def _get_or_create_salt() -> bytes:
    _SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _SALT_FILE.exists():
        return _SALT_FILE.read_bytes()
    salt = os.urandom(16)
    _SALT_FILE.write_bytes(salt)
    return salt


def derive_key(pin: str) -> bytes:
    """Derive a Fernet key from a PIN string using PBKDF2."""
    salt = _get_or_create_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,  # NIST-recommended minimum as of 2023
    )
    return base64.urlsafe_b64encode(kdf.derive(pin.encode()))


def hash_pin(pin: str) -> str:
    """Return a hex digest of the PIN for verification storage (not the key itself)."""
    salt = _get_or_create_salt()
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 390_000).hex()


def get_fernet(key: bytes) -> Fernet:
    return Fernet(key)


def encrypt_text(text: str, fernet: Fernet) -> bytes:
    return fernet.encrypt(text.encode("utf-8"))


def decrypt_text(data: bytes, fernet: Fernet) -> str:
    return fernet.decrypt(data).decode("utf-8")


def encrypt_file(path: Path, fernet: Fernet) -> None:
    """Encrypt a file in-place."""
    raw = path.read_bytes()
    path.write_bytes(fernet.encrypt(raw))


def decrypt_file(path: Path, fernet: Fernet) -> bytes:
    return fernet.decrypt(path.read_bytes())
