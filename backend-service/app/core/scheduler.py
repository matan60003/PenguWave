import asyncio
import logging
import random
import httpx
from datetime import datetime, timezone
from sqlalchemy import text
from app.database.database import SessionLocal, engine
from app.schemas import schemas
from app.services.event_service import EventService
from app.database.repositories import EventRepository

logger = logging.getLogger("penguwave")


async def _ping_db():
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            logger.debug("System Heartbeat: Database session is healthy")
    except Exception as e:
        logger.error(f"Heartbeat Database Session Error: {e}")


async def _ingest_vulnerabilities(vulnerabilities: list):
    if not vulnerabilities:
        return
        
    events_to_create = []
    for vuln in vulnerabilities:
        title = vuln.get("cveID", "Unknown CVE")
        description = vuln.get("shortDescription", "No description provided.")

        raw_date = vuln.get("dateAdded")
        if raw_date:
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                timestamp = dt.isoformat()
            except ValueError:

                timestamp = datetime.now(timezone.utc).isoformat()
        else:
            timestamp = datetime.now(timezone.utc).isoformat()

        severity = random.choice(["HIGH", "MEDIUM", "LOW"])
        source_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        assets = ["prod-web-01", "prod-db-02", "k8s-worker-node", "edge-router"]
        asset = random.choice(assets)

        event_create = schemas.EventCreate(
            timestamp=timestamp,
            severity=severity,
            title=title,
            description=description,
            assetHostname=asset,
            assetIp="10.0.0.1",
            sourceIp=source_ip,
            tags=["CISA", "KEV"],
            userId="usr-system",
        )
        events_to_create.append(event_create)
        
    try:
        async with SessionLocal() as db:
            event_repo = EventRepository(db)
            event_service = EventService(event_repo)
            added_count = await event_service.bulk_ingest_events(events_to_create)
            
            if added_count > 0:
                logger.info(f"Successfully ingested {added_count} new CISA KEV events.")
                await db.execute(text("NOTIFY new_events, '{\"type\"\: \"NEW_EVENTS\"}'"))
                await db.commit()
    except Exception:
        logger.error("Database error during CISA ingestion", exc_info=True)


async def _fetch_and_ingest_cisa_data():
    lock_db = None
    lock_acquired = False
    
    # Try to acquire an advisory lock to prevent multiple workers from running this simultaneously
    if engine.dialect.name == "postgresql":
        lock_db = SessionLocal()
        try:
           
            result = await lock_db.execute(text("SELECT pg_try_advisory_lock(1029384756)"))
            lock_acquired = result.scalar()
            if not lock_acquired:
                logger.debug("Another worker is running the CISA fetch. Skipping.")
                await lock_db.close()
                return
        except Exception:
            logger.error("Error acquiring lock", exc_info=True)
            await lock_db.close()
            return

    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    try:
       
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])

            await _ingest_vulnerabilities(vulnerabilities)
    except Exception:
        logger.error("Error fetching CISA data", exc_info=True)
    finally:
        if lock_db and lock_acquired:
            try:
                await lock_db.execute(text("SELECT pg_advisory_unlock(1029384756)"))
            except Exception:
                pass
            await lock_db.close()


async def heartbeat_task():
    logger.info("Background Task Scheduler Engine: Starting heartbeat task.")
    try:
        while True:
            logger.info("System Heartbeat: Scheduler is active")

            # Execute asynchronous DB operation
            await _ping_db()

            # Fetch and ingest real-time CISA telemetry
            await _fetch_and_ingest_cisa_data()

            # Wait for 300 seconds (5 minutes) before the next heartbeat
            await asyncio.sleep(300)
    except asyncio.CancelledError:
        logger.info("Background Task Scheduler Engine: Heartbeat task cancelled.")
