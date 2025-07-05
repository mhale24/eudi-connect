from datetime import datetime, timedelta
from typing import Any, Annotated
import base64

from jose import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Security

from eudi_connect.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API key hashing (using bcrypt for key hashing as well)
api_key_hasher = bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def hash_api_key(api_key: str) -> str:
    """Hash an API key."""
    return api_key_hasher.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return api_key_hasher.verify(plain_key, hashed_key)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its prefix."""
    import secrets
    
    # Generate a random API key
    api_key = f"eudi_live_{secrets.token_urlsafe(32)}"
    prefix = api_key[:16]  # First 16 characters as prefix
    
    return api_key, prefix


def _get_encryption_key() -> bytes:
    """Derive encryption key from the secret key."""
    password = settings.SECRET_KEY.get_secret_value().encode()
    salt = b'eudi_connect_salt'  # In production, use a random salt stored securely
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data using Fernet symmetric encryption."""
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt data: {str(e)}")


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using Fernet symmetric encryption."""
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")


async def get_current_merchant(
    api_key: "APIKey"
) -> "Merchant":
    """Dependency for getting the current merchant from API key."""
    return api_key.merchant
