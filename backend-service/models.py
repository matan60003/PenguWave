from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    """
    User database model representing application users.

    Attributes:
        id (str): Unique identifier (e.g., UUID or custom string).
        email (str): Unique and indexed email address of the user.
        hashed_password (str): Secure key-stretched bcrypt hash of the user's password.
        role (str): Role designation for Authorization/RBAC (e.g., 'admin', 'analyst', 'user').
        status (str): Status of the user account (e.g., 'active', 'suspended').
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r}, role={self.role!r})>"
