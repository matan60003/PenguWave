import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from pydantic import ValidationError
import jwt
import json

from app.core.lifespan import lifespan
from app.core.middleware import CorrelationIdMiddleware, correlation_id_ctx
from app.api import auth, users, events, websockets
from app.database.database import get_db
from app.core.exceptions import (
    NotFoundError,
    AuthError,
    ValidationError as DomainValidationError,
    PermissionError,
)


class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "correlation_id": correlation_id_ctx.get(None),
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

app.add_middleware(CorrelationIdMiddleware)


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


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": exc.detail},
    )


@app.exception_handler(AuthError)
async def auth_exception_handler(request, exc: AuthError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": exc.detail},
    )


@app.exception_handler(DomainValidationError)
async def domain_validation_exception_handler(request, exc: DomainValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.detail},
    )


@app.exception_handler(PermissionError)
async def permission_exception_handler(request, exc: PermissionError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": exc.detail},
    )


@app.get("/healthz", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
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
app.include_router(websockets.router)
