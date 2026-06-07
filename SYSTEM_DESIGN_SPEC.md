# PenguWave Technical Architecture & Design Specification

This document serves as the single source of truth for the PenguWave Full-Stack Security Operations Portal. It outlines the structural design, system flows, architectural trade-offs, and security modeling choices implemented in the platform, providing concrete code examples to illustrate how these theories operate in practice.

---

## 1. Detailed Project Structure & Folder Hierarchy

PenguWave operates as a decoupled monolith consisting of a React frontend and a FastAPI backend. The backend architecture strictly enforces a Separation of Concerns (SoC).

```text
PenguWave/
├── frontend/                     # React Frontend Application
│   └── src/                      # React Frontend Source
│       ├── api.ts                # Centralized network layer (fetch wrappers)
│       ├── components/           # Reusable UI components (Modals, Navbars)
│       └── pages/                # Core view layers (EventsPage.tsx, UsersPage.tsx)
├── backend-service/              # FastAPI Backend Server
│   ├── app/
│   │   ├── api/                  # Routing Layer: (e.g., events.py, auth.py) HTTP endpoints and dependencies
│   │   ├── core/                 # System Core: (e.g., lifespan.py, exceptions.py) Auth, Domain Exceptions
│   │   ├── database/             # Data Access Layer: (e.g., models.py, database.py) SQLAlchemy ORM setup
│   │   ├── schemas/              # Validation Layer: (e.g., schemas.py) Pydantic schemas for serialization
│   │   └── services/             # Business Logic Layer: (e.g., event_service.py) Core CRUD operations, throws domain exceptions
│   └── tests/                    # Automated Pytest suite (integration & unit)
└── docker-compose.yml            # Infrastructure orchestration
```

### Layer Responsibilities in Practice
*   **`app/api` (Routers):** Exclusively handles HTTP request parsing and translating domain exceptions to HTTP errors via global handlers.
*   **`app/schemas` (Pydantic):** Defined in `schemas.py`. Enforces data shape. If the frontend sends an invalid string for an email, Pydantic throws a `422 Unprocessable Entity` before the logic even runs.
*   **`app/services` (Business Logic):** Defined in `event_service.py`. Contains the actual algorithmic work. Completely decoupled from HTTP concerns (FastAPI), raising pure Python domain exceptions (e.g., `NotFoundError`).

---

## 2. System Flow & Request Lifecycle

### Typical API Request Lifecycle (e.g., Fetching Events)
Here is the exact path a request takes from the user's browser to the database and back.

1.  **Client Request (`frontend/src/api.ts`):** 
    The React frontend builds the URL parameters and attaches the JWT `Authorization` header.
    ```typescript
    export async function getEvents(page = 1, limit = 25, search = "") {
      const offset = (page - 1) * limit;
      const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
      if (search) params.append("search", search);
      // Fetches using our resilient fetchWithRetry wrapper
      return fetchWithRetry(`${API_URL}/api/events?${params.toString()}`);
    }
    ```

2.  **Routing & Auth Gate (`app/api/events.py`):** 
    FastAPI intercepts the request. The `Depends(get_current_user)` checks the JWT validity.
    ```python
    @router.get("", response_model=schemas.PaginatedEventsResponse)
    async def get_events(
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        db: Session = Depends(get_db),
    ):
        # The router does NO database logic, it delegates to the service layer
        return event_service.get_events(severity=None, search=search, limit=limit, offset=offset, db=db)
    ```

3.  **Business Logic & ORM (`app/services/event_service.py`):** 
    The service layer runs the dynamic SQLAlchemy query inside PostgreSQL.
    ```python
    def get_events(severity, search, limit, offset, db: Session):
        query = db.query(models.Event)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(models.Event.title.ilike(search_filter))
        total = query.count()
        events = query.order_by(models.Event.timestamp.desc()).offset(offset).limit(limit).all()
        return {"data": events, "total": total}
    ```

### Background Telemetry Ingestion Flow
PenguWave constantly polls the CISA Known Exploited Vulnerabilities (KEV) database without blocking the main web server.

1.  **Initialization (`app/core/lifespan.py`):** 
    When FastAPI boots, it binds the scheduler to the native `asyncio` event loop.
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Database boot logic...
        logger.info("Starting background scheduler...")
        scheduler_task = asyncio.create_task(heartbeat_task())
        yield
        scheduler_task.cancel()
    ```

2.  **Polling Loop (`app/core/scheduler.py`):** 
    The task loops indefinitely, using `httpx` for asynchronous HTTP requests.
    ```python
    async def heartbeat_task():
        while True:
            await _fetch_and_ingest_cisa_data()  # uses httpx.AsyncClient()
            await asyncio.sleep(300)             # Sleeps exactly 5 minutes non-blockingly
    ```

---

## 3. Design Decisions & Trade-offs (The "Why")

### Why FastAPI (Async) over Django (Sync)?
**Decision:** We chose FastAPI for the backend.
**Rationale:** Security telemetry systems are heavily I/O bound. Django's synchronous nature would block the main thread while waiting for the CISA database to respond over the network. FastAPI’s native `async`/`await` architecture allows it to pause the execution of one task (like fetching from CISA) to answer a React API request concurrently on the exact same thread.

### Why PostgreSQL (Relational) over NoSQL (e.g., MongoDB)?
**Decision:** Strict Relational SQL over schema-less Document stores.
**Rationale:** Security audit logs require absolute data integrity. We cannot afford "schema drift" where one event lacks a `severity` field. PostgreSQL guarantees rigid schemas, transactional rollbacks (so a failed bulk insert doesn't corrupt the database), and powerful `.ilike()` text searching.

### Why Server-Side Pagination over Client-Side?
**Decision:** We perform pagination (`limit`, `offset`) directly in PostgreSQL.
**Rationale:** While fetching all events and using `.filter().slice()` in React is easy to code, it fails at scale. If the CISA pipeline ingests 100,000 events, forcing the browser to download a 50MB JSON payload will crash the DOM.
**Implementation:** By using SQLAlchemy's `.offset()` and `.limit()` (as shown in section 2), the backend guarantees the frontend only downloads the exact 25 records required, capping memory usage permanently.

### Why native `asyncio` over Celery/Redis?
**Decision:** We run our background scheduler directly in FastAPI's event loop via `asyncio.create_task()`.
**Rationale:** Celery is industry-standard but requires deploying and monitoring two heavy infrastructure pieces: a Message Broker (Redis) and worker nodes. For a single scheduled polling script, this introduces massive operational overhead and failure points. Native `asyncio` achieves exactly what we need natively within the Python runtime.

---

## 4. Schema & Data Modeling

### UUIDs vs. Auto-Incrementing Integers
All Primary Keys in PenguWave use UUIDv4 strings.
**Implementation (`app/database/models.py`):**
```python
class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True) 
    # Example ID: "evt-f47ac10b-58cc-4372-a567-0e02b2c3d479"
```
**Rationale:** Sequential integers (1, 2, 3) expose the size of our database and open the door for IDOR (Insecure Direct Object Reference) enumeration attacks. UUIDs mathematically guarantee unguessable identifiers.

### Indexing Strategies
We applied B-Tree indexing to search targets, such as `userId` and `timestamp`.
**Rationale:** When searching the database for events assigned to a specific user, PostgreSQL would normally perform a full table scan (O(N) time complexity). A B-Tree index creates an organized lookup tree, dropping query times to O(log N) milliseconds.

---

## 5. Security & Infrastructure

### Authentication Flow (Bcrypt & JWT)
PenguWave uses a highly secure, stateless Authentication model.
*   **Bcrypt:** User passwords are computationally hashed. The database contains no plaintext passwords.
    ```python
    # In app/core/security.py
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    ```
*   **JWT (JSON Web Tokens):** The server signs a cryptographic JWT payload. The backend doesn't maintain a stateful session in memory. Every request from the frontend carries its own un-forgeable proof of identity inside the HTTP `Authorization` header.

### Infrastructure & Containerization (Docker)
We orchestrate the platform using `docker-compose.yml`.
*   **Environment Parity:** By wrapping the React app, Python API, and PostgreSQL database in Docker containers, we guarantee that the operating system dependencies used on an engineer's laptop are an exact 1:1 replica of what runs in production. This completely eliminates the notorious "it works on my machine" class of deployment failures.
