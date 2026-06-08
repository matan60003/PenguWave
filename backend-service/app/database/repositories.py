from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import models


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> models.User | None:
        result = await self.db.execute(
            select(models.User).filter(models.User.email == email)
        )
        return result.scalars().first()
