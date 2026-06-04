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
