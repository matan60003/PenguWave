import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("penguwave")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager to handle startup and shutdown events.
    Verifies database connection pool health on bootstrap.
    """
    logger.info("Verifying database connectivity on startup...")
    try:
        # Obtain a connection from the pool and run a baseline query
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connectivity verified successfully.")
    except Exception as e:
        logger.critical(f"Database bootstrap connection failed: {e}")
    yield


app = FastAPI(
    title="PenguWave API",
    description="Backend API for PenguWave Analyst Platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/healthz", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Deep health check endpoint.
    Runs a test query on the database using the connection pool to ensure
    container readiness and database availability.
    """
    try:
        # Execute a quick query using the request session
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check database verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is unavailable",
        )
