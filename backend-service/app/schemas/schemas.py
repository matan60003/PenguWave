from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    token: str
    user: UserResponse


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "analyst", "user"] = "user"


class UserUpdate(BaseModel):
    role: Optional[Literal["admin", "analyst", "user"]] = None
    status: Optional[Literal["active", "suspended"]] = None


class MessageResponse(BaseModel):
    message: str


class EventCreate(BaseModel):
    timestamp: str
    severity: str
    title: str
    description: str
    assetHostname: str
    assetIp: str
    sourceIp: str
    tags: list[str]
    userId: str


class EventResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)
