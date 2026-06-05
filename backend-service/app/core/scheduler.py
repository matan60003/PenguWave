import asyncio
import logging
from sqlalchemy import text
from app.database.database import SessionLocal

logger = logging.getLogger("penguwave")


def _ping_db():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            logger.debug("System Heartbeat: Database session is healthy")
    except Exception as e:
        logger.error(f"Heartbeat Database Session Error: {e}")


async def heartbeat_task():
    logger.info("Background Task Scheduler Engine: Starting heartbeat task.")
    try:
        while True:
            logger.info("System Heartbeat: Scheduler is active")

            # Execute synchronous DB operation in a threadpool to prevent blocking the async event loop
            await asyncio.to_thread(_ping_db)

            # Wait for 1 minute before the next heartbeat
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        logger.info("Background Task Scheduler Engine: Heartbeat task cancelled.")
