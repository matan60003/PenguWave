import uuid
from sqlalchemy.orm import Session
from app.core.exceptions import ValidationError, NotFoundError
from app.database import models
from app.schemas import schemas
from app.core import security


def get_all_users(db: Session):
    return db.query(models.User).all()


def create_user(user_data: schemas.UserCreate, db: Session):
    existing = (
        db.query(models.User).filter(models.User.email == user_data.email).first()
    )
    if existing:
        raise ValidationError("User with this email already exists")

    user_id = f"usr-{uuid.uuid4()}"
    new_user = models.User(
        id=user_id,
        email=user_data.email,
        hashed_password=security.hash_password(user_data.password),
        role=user_data.role,
        status="active",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(id: str, user_data: schemas.UserUpdate, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise NotFoundError("User not found")

    if user_data.role is not None:
        user.role = user_data.role
    if user_data.status is not None:
        user.status = user_data.status

    db.commit()
    db.refresh(user)
    return user


def delete_user(id: str, current_user_id: str, db: Session):
    if current_user_id == id:
        raise ValidationError("Cannot delete your own admin account")

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise NotFoundError("User not found")

    db.delete(user)
    db.commit()
