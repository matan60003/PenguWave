import uuid
from app.core.exceptions import ValidationError, NotFoundError
from app.database import models
from app.schemas import schemas
from app.core import security
from app.database.repositories import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_all_users(self):
        return await self.user_repo.get_all()

    async def create_user(self, user_data: schemas.UserCreate):
        existing = await self.user_repo.get_by_email(user_data.email)
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
        return await self.user_repo.create(new_user)

    async def update_user(self, id: str, user_data: schemas.UserUpdate):
        user = await self.user_repo.get_by_id(id)
        if not user:
            raise NotFoundError("User not found")

        if user_data.role is not None:
            user.role = user_data.role
        if user_data.status is not None:
            user.status = user_data.status

        return await self.user_repo.update(user)

    async def delete_user(self, id: str, current_user_id: str):
        if current_user_id == id:
            raise ValidationError("Cannot delete your own admin account")

        user = await self.user_repo.get_by_id(id)
        if not user:
            raise NotFoundError("User not found")

        await self.user_repo.delete(user)
