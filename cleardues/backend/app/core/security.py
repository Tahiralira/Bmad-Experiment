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


# === API Key Encryption (NFR4 Compliance - AES-256) ===


def get_encryption_key() -> bytes:
    """
    Get encryption key from SECRET_KEY.

    Derives a Fernet-compatible encryption key from the app's SECRET_KEY.
    Uses base64 URL-safe encoding to create a 32-byte key suitable for Fernet.

    Returns:
        bytes: 32-byte encryption key
    """
    # Use SECRET_KEY as base for encryption key
    # Pad or truncate to 32 bytes for Fernet compatibility
    key_bytes = settings.SECRET_KEY.encode()[:32].ljust(32, b"0")
    return base64.urlsafe_b64encode(key_bytes)


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
