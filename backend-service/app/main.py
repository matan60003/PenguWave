import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import ValidationError
import jwt
import json

from app.core.lifespan import lifespan
from app.api import auth, users, events
from app.database.database import get_db


class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONLogFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger("penguwave")

app = FastAPI(
    title="PenguWave API",
    description="Backend API for PenguWave Analyst Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5173/",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5173/",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    detail = exc.detail
    if detail == "Not authenticated":
        detail = "Authentication required"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    error_msg = "Validation error"
    if errors:
        err = errors[0]
        loc = " -> ".join(str(x) for x in err.get("loc", [])[1:])
        msg = err.get("msg", "invalid value")
        error_msg = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error_msg},
    )


@app.exception_handler(OperationalError)
async def operational_exception_handler(request, exc: OperationalError):
    logger.error(f"Database operational error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": "Database service is unavailable"},
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request, exc: ValidationError):
    logger.warning(f"Data validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Data validation failed"},
    )


@app.exception_handler(jwt.exceptions.PyJWTError)
async def jwt_exception_handler(request, exc: jwt.exceptions.PyJWTError):
    logger.warning(f"JWT error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Invalid authentication token"},
    )


@app.get("/healthz", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check database verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is unavailable",
        )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
