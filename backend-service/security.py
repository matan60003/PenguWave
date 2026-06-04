from passlib.context import CryptContext

# Set up CryptContext for secure password hashing using bcrypt.
# The deprecated='auto' option allows for seamless upgrading of hashing algorithms in the future
# if we decide to migrate to newer/stronger schemes.
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
