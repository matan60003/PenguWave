from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.schemas import schemas
from app.core import security


def authenticate_user(login_data: schemas.LoginRequest, db: Session) -> dict:
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if not user or not security.verify_password(
        login_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = security.create_access_token(data={"sub": user.id, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "token": token,
        "user": user,
    }
