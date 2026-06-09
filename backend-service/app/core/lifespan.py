import json
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text, select

from app.core.config import settings
from app.database.database import SessionLocal, Base, engine
from app.database import models
from app.core import security
from app.core.scheduler import heartbeat_task
import asyncpg
from app.core.websockets import manager

logger = logging.getLogger("penguwave")


def load_mock_events() -> list[dict]:
    config_path = Path(settings.MOCK_EVENTS_PATH)

    if not config_path.is_absolute():
        base_dir = Path(__file__).resolve().parent
        resolved_path = (base_dir / config_path).resolve()
    else:
        resolved_path = config_path.resolve()

    if resolved_path.suffix != ".json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security error: Invalid file type specified.",
        )

    project_root = Path(__file__).resolve().parent.parent.parent.parent.resolve()
    if project_root == Path("/"):
        project_root = Path("/app").resolve()

    if not str(resolved_path).startswith(str(project_root)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security error: Path traversal detected.",
        )

    if not resolved_path.exists():
        logger.error(f"Mock events file not found at: {resolved_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security events file not found.",
        )

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse mock events JSON file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse mock events data.",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            admin_email = "admin@penguwave.com"
            result = await db.execute(
                select(models.User).filter(models.User.email == admin_email)
            )
            existing_user = result.scalars().first()
            if not existing_user:
                logger.info(f"Seeding default admin user: {admin_email}")
                default_admin = models.User(
                    id="usr-admin",
                    email=admin_email,
                    hashed_password=security.hash_password("adminpassword"),
                    role="admin",
                    status="active",
                )
                db.add(default_admin)
                await db.commit()
                logger.info("Default admin user successfully seeded.")
                
            system_email = "system@penguwave.com"
            result_sys = await db.execute(
                select(models.User).filter(models.User.email == system_email)
            )
            existing_sys = result_sys.scalars().first()
            if not existing_sys:
                logger.info(f"Seeding default system user: {system_email}")
                default_system = models.User(
                    id="usr-system",
                    email=system_email,
                    hashed_password=security.hash_password("systempassword"),
                    role="admin",
                    status="active",
                )
                db.add(default_system)
                await db.commit()
                logger.info("Default system user successfully seeded.")

            result = await db.execute(select(models.Event).limit(1))
            existing_event = result.scalars().first()
            if not existing_event:
                logger.info("Seeding security events from JSON...")
                try:
                    events_data = load_mock_events()
                    for evt in events_data:
                        db_evt = models.Event(
                            id=evt["id"],
                            timestamp=evt["timestamp"],
                            severity=evt["severity"],
                            title=evt["title"],
                            description=evt["description"],
                            assetHostname=evt["assetHostname"],
                            assetIp=evt["assetIp"],
                            sourceIp=evt["sourceIp"],
                            tags=evt["tags"],
                            userId=evt["userId"],
                        )
                        db.add(db_evt)
                    await db.commit()
                    logger.info("Security events successfully seeded.")
                except Exception as ex_seed:
                    logger.error(f"Failed to seed security events: {ex_seed}")
        logger.info("Database bootstrap completed successfully.")
    except Exception as e:
        logger.critical(f"Database bootstrap failed: {e}")

    logger.info("Starting background scheduler...")
    scheduler_task = asyncio.create_task(heartbeat_task())

    async def listen_for_events():
        dsn = settings.DATABASE_URL.replace("+asyncpg", "")
        try:
            conn = await asyncpg.connect(dsn)
            def handle_notification(connection, pid, channel, payload):
                logger.info(f"Received notification on channel {channel}: {payload}")
                asyncio.create_task(manager.broadcast(payload))

            await conn.add_listener('new_events', handle_notification)
            logger.info("Listening for PostgreSQL notifications on 'new_events'...")
            while True:
                await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in PostgreSQL listener: {e}")

    listener_task = asyncio.create_task(listen_for_events())

    yield

    logger.info("Shutting down background scheduler...")
    scheduler_task.cancel()
    listener_task.cancel()
    try:
        await scheduler_task
        await listener_task
    except asyncio.CancelledError:
        pass
    logger.info("Background tasks shut down completely.")
