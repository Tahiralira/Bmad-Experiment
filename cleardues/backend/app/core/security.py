import base64
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# === API key encryption at rest ===
#
# Fernet = AES-128-CBC + HMAC-SHA256. (The old "AES-256 / NFR4" claims were
# false — review B-C5/S5-C1; NFR4 should be read as "encrypted at rest".)
#
# The Fernet key is derived with HKDF-SHA256 from a dedicated ENCRYPTION_KEY
# setting, with a fixed salt + info label for domain separation — a leaked
# JWT-signing secret no longer compromises stored API keys, and rotating
# SECRET_KEY no longer bricks them. In local dev ENCRYPTION_KEY may be unset;
# we fall back to deriving from SECRET_KEY (config fails fast outside local).
#
# Migration note (B-C5): no production data exists under the old
# truncate-pad-SECRET_KEY scheme — the review confirmed no write path ever
# shipped (B-C2), so encrypted keys only ever existed inside test runs.
# There is deliberately no legacy-decrypt fallback.


def get_encryption_key() -> bytes:
    """Derive the Fernet key (urlsafe-b64, 32 bytes) via HKDF-SHA256."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    secret = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"cleardues.fernet.v1",
        info=b"api-key-encryption",
    )
    return base64.urlsafe_b64encode(hkdf.derive(secret.encode()))


# Initialize Fernet instance with derived key
_fernet = Fernet(get_encryption_key())


def encrypt_api_key(plaintext: str) -> str:
    """
    Encrypt API key for storage.

    Uses Fernet symmetric encryption (AES-128 in CBC mode with HMAC).
    The encrypted key can be safely stored in the database.

    Args:
        plaintext: The API key to encrypt

    Returns:
        str: URL-safe encrypted API key (base64-encoded)

    Example:
        >>> encrypted = encrypt_api_key("AIzaSyC...")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    """
    Decrypt API key for use.

    Decrypts an API key that was encrypted with encrypt_api_key().

    Args:
        encrypted: The encrypted API key string

    Returns:
        str: The decrypted plaintext API key

    Raises:
        cryptography.fernet.InvalidToken: If the key is corrupted or tampered with

    Example:
        >>> decrypted = decrypt_api_key(encrypted)
        >>> print(decrypted)
        'AIzaSyC...'
    """
    return _fernet.decrypt(encrypted.encode()).decode()
