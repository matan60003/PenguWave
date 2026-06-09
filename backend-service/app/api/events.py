from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.database import get_db
from app.schemas import schemas
from app.api.dependencies import get_current_user, require_admin
from app.database.repositories import EventRepository
from app.services.event_service import EventService

router = APIRouter(
    prefix="/api/events", tags=["Events"], dependencies=[Depends(get_current_user)]
)


def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)


@router.get("", response_model=schemas.PaginatedEventsResponse)
async def get_events(
    severity: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    event_service: EventService = Depends(get_event_service),
):
    if limit is not None:
        limit = min(limit, 100)
    return await event_service.get_events(severity, search, limit, offset)


@router.post(
    "",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_event(
    event_data: schemas.EventCreate,
    event_service: EventService = Depends(get_event_service),
    db: AsyncSession = Depends(get_db),
):
    result = await event_service.create_event(event_data)
    await db.execute(text('NOTIFY new_events, \'{"type": "NEW_EVENTS"}\''))
    await db.commit()
    await db.refresh(result)
    return result


@router.get("/{id}", response_model=schemas.EventResponse)
async def get_event(id: str, event_service: EventService = Depends(get_event_service)):
    return await event_service.get_event(id)


@router.delete(
    "/{id}",
    response_model=schemas.MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_event(
    id: str,
    event_service: EventService = Depends(get_event_service),
    db: AsyncSession = Depends(get_db),
):
    await event_service.delete_event(id)
    await db.execute(text('NOTIFY new_events, \'{"type": "NEW_EVENTS"}\''))
    await db.commit()
    return {"message": "Event deleted"}
