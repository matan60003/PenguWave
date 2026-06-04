import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database.database import Base
from app.schemas.schemas import EventCreate
from app.services import event_service

# Setup in-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_and_get_event(db):
    event_data = EventCreate(
        timestamp="2026-06-04T12:00:00Z",
        severity="HIGH",
        title="Unauthorized Access",
        description="Login attempt from unauthorized IP",
        assetHostname="server01",
        assetIp="192.168.1.10",
        sourceIp="10.0.0.5",
        tags=["auth", "security"],
        userId="usr-admin",
    )

    # Test creation
    created_event = event_service.create_event(event_data, db)
    assert created_event.id.startswith("evt-")
    assert created_event.severity == "HIGH"
    assert created_event.title == "Unauthorized Access"

    # Test retrieval
    fetched_event = event_service.get_event(created_event.id, db)
    assert fetched_event.id == created_event.id
    assert fetched_event.description == "Login attempt from unauthorized IP"


def test_get_events_list(db):
    # Create multiple events
    for severity in ["LOW", "HIGH", "CRITICAL"]:
        event_data = EventCreate(
            timestamp="2026-06-04T12:00:00Z",
            severity=severity,
            title=f"Event {severity}",
            description="test",
            assetHostname="test",
            assetIp="1.1.1.1",
            sourceIp="1.1.1.1",
            tags=[],
            userId="test",
        )
        event_service.create_event(event_data, db)

    events = event_service.get_events(severity=None, limit=10, offset=0, db=db)
    assert len(events) == 3

    # Test filtering by severity
    high_events = event_service.get_events(severity="HIGH", limit=10, offset=0, db=db)
    assert len(high_events) == 1
    assert high_events[0].severity == "HIGH"


def test_delete_event(db):
    event_data = EventCreate(
        timestamp="2026-06-04T12:00:00Z",
        severity="LOW",
        title="To be deleted",
        description="test",
        assetHostname="test",
        assetIp="1.1.1.1",
        sourceIp="1.1.1.1",
        tags=[],
        userId="test",
    )
    created = event_service.create_event(event_data, db)

    # Delete it
    event_service.delete_event(created.id, db)

    # Verify deletion
    with pytest.raises(HTTPException) as exc_info:
        event_service.get_event(created.id, db)

    assert exc_info.value.status_code == 404
