from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import models


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> models.User | None:
        result = await self.db.execute(
            select(models.User).filter(models.User.email == email)
        )
        return result.scalars().first()

    async def get_all(self) -> list[models.User]:
        result = await self.db.execute(select(models.User))
        return result.scalars().all()

    async def get_by_id(self, id: str) -> models.User | None:
        result = await self.db.execute(select(models.User).filter(models.User.id == id))
        return result.scalars().first()

    async def create(self, user: models.User) -> models.User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: models.User) -> models.User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: models.User) -> None:
        await self.db.delete(user)
        await self.db.commit()


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_events(
        self,
        severity: str | None,
        search: str | None,
        limit: int | None,
        offset: int | None,
    ) -> dict:
        query = select(models.Event)
        if severity:
            query = query.filter(models.Event.severity == severity.upper())
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    models.Event.title.ilike(search_filter),
                    models.Event.description.ilike(search_filter),
                    models.Event.assetHostname.ilike(search_filter),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(models.Event.timestamp.desc(), models.Event.id)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.db.execute(query)
        events = result.scalars().all()
        return {"data": events, "total": total}

    async def get_by_id(self, id: str) -> models.Event | None:
        result = await self.db.execute(select(models.Event).filter(models.Event.id == id))
        return result.scalars().first()

    async def create(self, event: models.Event) -> models.Event:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def delete(self, event: models.Event) -> None:
        await self.db.delete(event)
        await self.db.commit()

    async def get_existing_titles(self, titles: list[str]) -> set[str]:
        if not titles:
            return set()
        
        existing_titles = set()
        chunk_size = 100
        for i in range(0, len(titles), chunk_size):
            chunk = titles[i:i + chunk_size]
            result = await self.db.execute(
                select(models.Event.title).filter(models.Event.title.in_(chunk))
            )
            existing_titles.update(result.scalars().all())
            
        return existing_titles

    async def bulk_create(self, events: list[models.Event]) -> None:
        if not events:
            return
        self.db.add_all(events)
        await self.db.commit()
