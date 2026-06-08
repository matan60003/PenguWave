import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.exceptions import ValidationError, NotFoundError
from app.database import models
from app.schemas import schemas
from app.core import security


async def get_all_users(db: AsyncSession):
    result = await db.execute(select(models.User))
    return result.scalars().all()


async def create_user(user_data: schemas.UserCreate, db: AsyncSession):
    result = await db.execute(
        select(models.User).filter(models.User.email == user_data.email)
    )
    existing = result.scalars().first()
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
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_user(id: str, user_data: schemas.UserUpdate, db: AsyncSession):
    result = await db.execute(select(models.User).filter(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise NotFoundError("User not found")

    if user_data.role is not None:
        user.role = user_data.role
    if user_data.status is not None:
        user.status = user_data.status

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(id: str, current_user_id: str, db: AsyncSession):
    if current_user_id == id:
        raise ValidationError("Cannot delete your own admin account")

    result = await db.execute(select(models.User).filter(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise NotFoundError("User not found")

    await db.delete(user)
    await db.commit()
