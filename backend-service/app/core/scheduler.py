import asyncio
import logging
import random
import uuid
import httpx
from datetime import datetime, timezone
from sqlalchemy import text
from app.database.database import SessionLocal
from app.database import models

logger = logging.getLogger("penguwave")


def _ping_db():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            logger.debug("System Heartbeat: Database session is healthy")
    except Exception as e:
        logger.error(f"Heartbeat Database Session Error: {e}")


def _ingest_vulnerabilities(vulnerabilities: list):
    try:
        with SessionLocal() as db:
            added_count = 0
            for vuln in vulnerabilities:
                title = vuln.get("cveID", "Unknown CVE")

                # Deduplication: Check if event with this title exists
                existing = (
                    db.query(models.Event).filter(models.Event.title == title).first()
                )
                if existing:
                    continue

                description = vuln.get("shortDescription", "No description provided.")

                raw_date = vuln.get("dateAdded")
                if raw_date:
                    try:
                        dt = datetime.strptime(raw_date, "%Y-%m-%d").replace(
                            tzinfo=timezone.utc
                        )
                        timestamp = dt.isoformat()
                    except ValueError:
                        timestamp = datetime.now(timezone.utc).isoformat()
                else:
                    timestamp = datetime.now(timezone.utc).isoformat()

                severity = random.choice(["HIGH", "MEDIUM", "LOW"])
                source_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                assets = ["prod-web-01", "prod-db-02", "k8s-worker-node", "edge-router"]
                asset = random.choice(assets)

                new_event = models.Event(
                    id=f"evt-{uuid.uuid4()}",
                    timestamp=timestamp,
                    severity=severity,
                    title=title,
                    description=description,
                    assetHostname=asset,
                    assetIp="10.0.0.1",
                    sourceIp=source_ip,
                    tags=["CISA", "KEV"],
                    userId="usr-admin",
                )
                db.add(new_event)
                added_count += 1

            db.commit()
            if added_count > 0:
                logger.info(f"Successfully ingested {added_count} new CISA KEV events.")
    except Exception as e:
        logger.error(f"Database error during CISA ingestion: {e}")


async def _fetch_and_ingest_cisa_data():
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])

            await asyncio.to_thread(_ingest_vulnerabilities, vulnerabilities)
    except Exception as e:
        logger.error(f"Error fetching CISA data: {e}")


async def heartbeat_task():
    logger.info("Background Task Scheduler Engine: Starting heartbeat task.")
    try:
        while True:
            logger.info("System Heartbeat: Scheduler is active")

            # Execute synchronous DB operation in a threadpool to prevent blocking the async event loop
            await asyncio.to_thread(_ping_db)

            # Fetch and ingest real-time CISA telemetry
            await _fetch_and_ingest_cisa_data()

            # Wait for 300 seconds (5 minutes) before the next heartbeat
            await asyncio.sleep(300)
    except asyncio.CancelledError:
        logger.info("Background Task Scheduler Engine: Heartbeat task cancelled.")
