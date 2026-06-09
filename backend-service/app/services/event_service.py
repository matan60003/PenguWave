import uuid
from app.core.exceptions import NotFoundError
from app.database import models
from app.schemas import schemas
from app.database.repositories import EventRepository


class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def get_events(
        self,
        severity: str | None,
        search: str | None,
        limit: int | None,
        offset: int | None,
    ):
        return await self.event_repo.get_events(severity, search, limit, offset)

    async def create_event(self, event_data: schemas.EventCreate):
        event_id = f"evt-{uuid.uuid4()}"
        new_event = models.Event(
            id=event_id,
            timestamp=event_data.timestamp,
            severity=event_data.severity,
            title=event_data.title,
            description=event_data.description,
            assetHostname=event_data.assetHostname,
            assetIp=event_data.assetIp,
            sourceIp=event_data.sourceIp,
            tags=event_data.tags,
            userId=event_data.userId,
        )
        return await self.event_repo.create(new_event)

    async def get_event(self, id: str):
        event = await self.event_repo.get_by_id(id)
        if not event:
            raise NotFoundError("Event not found")
        return event

    async def delete_event(self, id: str):
        event = await self.event_repo.get_by_id(id)
        if not event:
            raise NotFoundError("Event not found")
        await self.event_repo.delete(event)

    async def bulk_ingest_events(self, events_data: list[schemas.EventCreate]) -> int:
        if not events_data:
            return 0
            
        titles = [e.title for e in events_data]
       
        existing_titles = await self.event_repo.get_existing_titles(titles)
        
        new_events = []
        for event_data in events_data:
            if event_data.title in existing_titles:
                continue
                

            event_id = f"evt-{uuid.uuid4()}"
            new_event = models.Event(
                id=event_id,
                timestamp=event_data.timestamp,
                severity=event_data.severity,
                title=event_data.title,
                description=event_data.description,
                assetHostname=event_data.assetHostname,
                assetIp=event_data.assetIp,
                sourceIp=event_data.sourceIp,
                tags=event_data.tags,
                userId=event_data.userId,
            )
            new_events.append(new_event)
            
        if new_events:
            await self.event_repo.bulk_create(new_events)
            
        return len(new_events)
