import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, get_db, Base, engine
import models
import schemas
import security

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("penguwave")

# Security scheme for JWT extraction from Bearer Token
security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Dependency injection helper to authenticate requests.
    Decodes the Bearer JWT token and retrieves the current user from the database.
    """
    token = credentials.credentials
    payload = security.decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager to handle startup and shutdown events.
    Creates tables and seeds a default admin user if none exist.
    """
    logger.info("Initializing database schema...")
    try:
        # Create all tables defined in models.py
        Base.metadata.create_all(bind=engine)

        # Verify connection and seed data
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

            # Check if default admin user needs to be seeded
            admin_email = "admin@penguwave.com"
            existing_user = (
                db.query(models.User).filter(models.User.email == admin_email).first()
            )
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
                db.commit()
                logger.info("Default admin user successfully seeded.")
        logger.info("Database bootstrap completed successfully.")
    except Exception as e:
        logger.critical(f"Database bootstrap failed: {e}")
    yield


app = FastAPI(
    title="PenguWave API",
    description="Backend API for PenguWave Analyst Platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Format HTTPExceptions to follow the { "error": "message" } API contract format.
    """
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
    """
    Format Pydantic RequestValidationErrors to follow the { "error": "message" } API contract format.
    """
    errors = exc.errors()
    error_msg = "Validation error"
    if errors:
        err = errors[0]
        # Build a descriptive path skipping 'body', e.g. "email: value is not a valid email address"
        loc = " -> ".join(str(x) for x in err.get("loc", [])[1:])
        msg = err.get("msg", "invalid value")
        error_msg = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error_msg},
    )


@app.get("/healthz", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Deep health check endpoint.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check database verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection is unavailable",
        )


@app.post(
    "/api/auth/login", response_model=schemas.LoginResponse, tags=["Authentication"]
)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and start a session by returning a signed JWT access token.
    """
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if not user or not security.verify_password(
        login_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create signed token with user id as the subject
    token = security.create_access_token(data={"sub": user.id, "role": user.role})

    return {"token": token, "user": user}


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout():
    """
    End the current session (stateless logout endpoint).
    """
    return {"message": "Logged out"}


@app.get("/api/auth/me", response_model=schemas.UserResponse, tags=["Authentication"])
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Get the currently authenticated user's info from the decoded bearer token.
    """
    return current_user
