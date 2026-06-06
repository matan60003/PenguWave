from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas import schemas
from app.api.dependencies import get_current_user, require_admin
from app.services import event_service

router = APIRouter(
    prefix="/api/events", tags=["Events"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=schemas.PaginatedEventsResponse)
async def get_events(
    severity: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    db: Session = Depends(get_db),
):
    return event_service.get_events(severity, search, limit, offset, db)


@router.post(
    "",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_event(
    event_data: schemas.EventCreate,
    db: Session = Depends(get_db),
):
    return event_service.create_event(event_data, db)


@router.get("/{id}", response_model=schemas.EventResponse)
async def get_event(id: str, db: Session = Depends(get_db)):
    return event_service.get_event(id, db)


@router.delete(
    "/{id}",
    response_model=schemas.MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_event(id: str, db: Session = Depends(get_db)):
    event_service.delete_event(id, db)
    return {"message": "Event deleted"}
