from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas import schemas
from app.database import models
from app.database.repositories import UserRepository
from app.api.dependencies import get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    login_data: schemas.LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> schemas.LoginResponse:
    return auth_service.authenticate_user(login_data)


@router.post("/logout", response_model=schemas.MessageResponse)
async def logout(
    current_user: models.User = Depends(get_current_user),
) -> schemas.MessageResponse:
    return schemas.MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(
    current_user: models.User = Depends(get_current_user),
) -> schemas.UserResponse:
    return schemas.UserResponse.model_validate(current_user)
