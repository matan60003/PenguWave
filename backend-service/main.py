import json
import logging
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
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


def require_role(allowed_roles: list[str]):
    """
    Dependency helper that validates if the authenticated user has an authorized role.
    Raises a 403 Forbidden with uniform formatting if unauthorized.
    """

    def dependency(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized (wrong role)",
            )
        return current_user

    return dependency


require_admin = Depends(require_role(["admin"]))


def load_mock_events() -> list[dict]:
    """
    Safely load events from the mock events JSON file.
    Enforces validation checks against path traversal and file type constraints.
    """
    config_path = Path(settings.MOCK_EVENTS_PATH)

    # Resolve the absolute path
    if not config_path.is_absolute():
        base_dir = Path(__file__).resolve().parent
        resolved_path = (base_dir / config_path).resolve()
    else:
        resolved_path = config_path.resolve()

    # Enforce strictly JSON suffix to mitigate arbitrary file reads
    if resolved_path.suffix != ".json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security error: Invalid file type specified.",
        )

    # Safe path boundary validation (path traversal check)
    # The path must reside inside the project workspace directory.
    project_root = Path(__file__).resolve().parent.parent.resolve()
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

            # Check if security events need to be seeded
            existing_event = db.query(models.Event).first()
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
                    db.commit()
                    logger.info("Security events successfully seeded.")
                except Exception as ex_seed:
                    logger.error(f"Failed to seed security events: {ex_seed}")
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

# Configure CORS Middleware to allow requests from local frontend servers
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

    return {
        "access_token": token,
        "token_type": "bearer",
        "token": token,
        "user": user,
    }


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


@app.get(
    "/api/users",
    response_model=list[schemas.UserResponse],
    tags=["Users"],
    dependencies=[require_admin],
)
async def get_users(db: Session = Depends(get_db)):
    """
    Get the list of all users. Admin-only.
    """
    return db.query(models.User).all()


@app.post(
    "/api/users",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
    dependencies=[require_admin],
)
async def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user. Admin-only.
    """
    # Check if user already exists
    existing = (
        db.query(models.User).filter(models.User.email == user_data.email).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Generate a unique usr- prefix ID
    user_id = f"usr-{uuid.uuid4()}"
    new_user = models.User(
        id=user_id,
        email=user_data.email,
        hashed_password=security.hash_password(user_data.password),
        role=user_data.role,
        status="active",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.patch(
    "/api/users/{id}",
    response_model=schemas.UserResponse,
    tags=["Users"],
    dependencies=[require_admin],
)
async def update_user(
    id: str, user_data: schemas.UserUpdate, db: Session = Depends(get_db)
):
    """
    Update a user's role or status. Admin-only.
    """
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.role is not None:
        user.role = user_data.role
    if user_data.status is not None:
        user.status = user_data.status

    db.commit()
    db.refresh(user)
    return user


@app.delete(
    "/api/users/{id}",
    response_model=schemas.MessageResponse,
    tags=["Users"],
)
async def delete_user(
    id: str,
    current_user: models.User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Delete a user. Admin-only. Blocks self-deletion.
    """
    if current_user.id == id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account",
        )

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@app.get(
    "/api/events",
    response_model=list[schemas.EventResponse],
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)
async def get_events(
    severity: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Get the list of security events from PostgreSQL.
    Supports optional severity filtering and limit/offset pagination.
    """
    query = db.query(models.Event)

    if severity:
        query = query.filter(models.Event.severity == severity.upper())

    # Sort by ID to ensure stable ordering matching JSON sequence
    query = query.order_by(models.Event.id)

    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    return query.all()


@app.post(
    "/api/events",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)
async def create_event(
    event_data: schemas.EventCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new security event in PostgreSQL.
    """
    # Generate a unique event ID (evt-...)
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


@app.get(
    "/api/events/{id}",
    response_model=schemas.EventResponse,
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)
async def get_event(id: str, db: Session = Depends(get_db)):
    """
    Get a single security event by ID from PostgreSQL.
    Raises 404 if the event is not found.
    """
    event = db.query(models.Event).filter(models.Event.id == id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@app.delete(
    "/api/events/{id}",
    response_model=schemas.MessageResponse,
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)
async def delete_event(id: str, db: Session = Depends(get_db)):
    """
    Delete a security event from PostgreSQL.
    """
    event = db.query(models.Event).filter(models.Event.id == id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}
