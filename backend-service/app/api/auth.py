from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas import schemas
from app.database import models
from app.api.dependencies import get_current_user
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=schemas.LoginResponse)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    return auth_service.authenticate_user(login_data, db)


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
