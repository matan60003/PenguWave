import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import models
from app.schemas import schemas


def get_events(
    severity: str | None, limit: int | None, offset: int | None, db: Session
):
    query = db.query(models.Event)
    if severity:
        query = query.filter(models.Event.severity == severity.upper())
    query = query.order_by(models.Event.id)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def create_event(event_data: schemas.EventCreate, db: Session):
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
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


def get_event(id: str, db: Session):
    event = db.query(models.Event).filter(models.Event.id == id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def delete_event(id: str, db: Session):
    event = db.query(models.Event).filter(models.Event.id == id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    db.delete(event)
    db.commit()
