from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext

from config import settings

# Set up CryptContext for secure password hashing using bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using the key-stretched bcrypt algorithm.
    Automatically generates a unique salt per password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext candidate password against the stored bcrypt hash.
    Protects against timing attacks by using constant-time comparison under the hood.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generates a secure, cryptographically signed JSON Web Token (JWT).
    Sets the exp (expiration) claim using timezone-aware UTC datetime.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})

    # Sign the token using our HS256 key
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT token.
    Returns the payload dictionary if signature and expiration are valid,
    otherwise returns None.
    """
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return None
