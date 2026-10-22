"""
Security utilities: JWT creation/validation, OAuth token encryption.
Tokens are encrypted at rest — never stored or logged as plaintext.
"""
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def _get_fernet() -> Fernet:
    raw_key = (settings.token_encryption_key or settings.encryption_key).encode()
    # Pad/trim to valid 32-byte key and base64-encode for Fernet
    key = base64.urlsafe_b64encode(raw_key[:32].ljust(32, b"="))
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt an OAuth token for storage using TOKEN_ENCRYPTION_KEY."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored OAuth token for use."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        import hashlib
        return "sha256$" + hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    if hashed.startswith("sha256$"):
        import hashlib
        return hashed == "sha256$" + hashlib.sha256(plain.encode()).hexdigest()
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False
