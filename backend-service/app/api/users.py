from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas import schemas
from app.database import models
from app.api.dependencies import require_admin
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get(
    "", response_model=list[schemas.UserResponse], dependencies=[Depends(require_admin)]
)
async def get_users(db: AsyncSession = Depends(get_db)):
    return await user_service.get_all_users(db)


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(
    user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)
):
    return await user_service.create_user(user_data, db)


@router.patch(
    "/{id}", response_model=schemas.UserResponse, dependencies=[Depends(require_admin)]
)
async def update_user(
    id: str, user_data: schemas.UserUpdate, db: AsyncSession = Depends(get_db)
):
    return await user_service.update_user(id, user_data, db)


@router.delete("/{id}", response_model=schemas.MessageResponse)
async def delete_user(
    id: str,
    current_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await user_service.delete_user(id, current_user.id, db)
    return {"message": "User deleted"}
