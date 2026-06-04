from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r}, role={self.role!r})>"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    assetHostname: Mapped[str] = mapped_column(String, nullable=False)
    assetIp: Mapped[str] = mapped_column(String, nullable=False)
    sourceIp: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    userId: Mapped[str] = mapped_column(String, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<Event(id={self.id!r}, severity={self.severity!r}, title={self.title!r})>"
        )
