import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.exceptions import NotFoundError
from app.database import models
from app.schemas import schemas


async def get_events(
    severity: str | None,
    search: str | None,
    limit: int | None,
    offset: int | None,
    db: AsyncSession,
):
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
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(models.Event.timestamp.desc(), models.Event.id)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()
    return {"data": events, "total": total}


async def create_event(event_data: schemas.EventCreate, db: AsyncSession):
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
    await db.commit()
    await db.refresh(new_event)
    return new_event


async def get_event(id: str, db: AsyncSession):
    result = await db.execute(select(models.Event).filter(models.Event.id == id))
    event = result.scalars().first()
    if not event:
        raise NotFoundError("Event not found")
    return event


async def delete_event(id: str, db: AsyncSession):
    result = await db.execute(select(models.Event).filter(models.Event.id == id))
    event = result.scalars().first()
    if not event:
        raise NotFoundError("Event not found")
    await db.delete(event)
    await db.commit()
