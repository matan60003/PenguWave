from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas import schemas
from app.database import models
from app.api.dependencies import require_admin
from app.database.repositories import UserRepository
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


@router.get(
    "", response_model=list[schemas.UserResponse], dependencies=[Depends(require_admin)]
)
async def get_users(user_service: UserService = Depends(get_user_service)):
    return await user_service.get_all_users()


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(
    user_data: schemas.UserCreate, user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user_data)


@router.patch(
    "/{id}", response_model=schemas.UserResponse, dependencies=[Depends(require_admin)]
)
async def update_user(
    id: str,
    user_data: schemas.UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.update_user(id, user_data)


@router.delete("/{id}", response_model=schemas.MessageResponse)
async def delete_user(
    id: str,
    current_user: models.User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.delete_user(id, current_user.id)
    return {"message": "User deleted"}
