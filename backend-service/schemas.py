from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    """
    Request payload model for user login.
    Enforces valid email format validation.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Public user representation model.
    Excludes sensitive fields like password hashes.
    """

    id: str
    email: EmailStr
    role: str
    status: str

    # Enables Pydantic to read data from ORM objects (SQLAlchemy model instances)
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """
    Success response model for authentication.
    Returns the JWT token and the public user profile.
    """

    token: str
    user: UserResponse


class UserCreate(BaseModel):
    """
    Request payload model for user creation.
    Enforces valid email formatting and specific roles.
    """

    email: EmailStr
    password: str
    role: Literal["admin", "analyst", "user"] = "user"


class UserUpdate(BaseModel):
    """
    Request payload model for user updates.
    Allows modifying either role or status, or both.
    """

    role: Optional[Literal["admin", "analyst", "user"]] = None
    status: Optional[Literal["active", "suspended"]] = None


class MessageResponse(BaseModel):
    """
    Standard success message response.
    """

    message: str


class EventResponse(BaseModel):
    """
    Representational response schema for a security event.
    """

    id: str
    timestamp: str
    severity: str
    title: str
    description: str
    assetHostname: str
    assetIp: str
    sourceIp: str
    tags: list[str]
    userId: str
