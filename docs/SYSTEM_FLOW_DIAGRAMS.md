# PenguWave System Flow Diagrams

This document contains visual diagrams mapping out the critical communication paths between the different layers of the PenguWave architecture.

---

## 1. User API Request Lifecycle (Fetching Events)

This diagram illustrates the  Architecture flow. Notice how the request moves strictly through defined layers (Frontend -> Router -> Service -> Repository -> Database) without skipping steps.

```mermaid
sequenceDiagram
    autonumber
    participant Browser as React Frontend
    participant Router as API Router (events.py)
    participant Auth as Auth Gate (dependencies.py)
    participant Service as EventService
    participant Repo as EventRepository
    participant DB as PostgreSQL DB

    Browser->>Router: GET /api/events (with JWT in Header)
    
    rect rgba(233, 206, 206, 1)
    Note over Router,Auth: 1. Security Layer
    Router->>Auth: Verify Token & User Status
    Auth-->>Router: Valid User Object
    end

    rect rgba(200, 206, 213, 1)
    Note over Router,Service: 2. Routing Layer
    Router->>Service: get_events(limit, offset, search)
    end
    
    rect rgba(194, 208, 194, 1)
    Note over Service,Repo: 3. Business & Data Layer
    Service->>Repo: get_events(limit, offset, search)
    Repo->>DB: Execute SQLAlchemy select(...) with limit/offset
    DB-->>Repo: Returns Raw Event Rows & Total Count
    Repo-->>Service: Python Dictionary (data & total)
    end
    
    Service-->>Router: Validated Pydantic Response
    Router-->>Browser: JSON payload (200 OK)
```

---

## 2. Background Telemetry Ingestion Flow

This diagram illustrates how the asynchronous background task runs silently alongside the main web server, guaranteeing deduplication and avoiding concurrency collisions using PostgreSQL locks.

```mermaid
sequenceDiagram
    autonumber
    participant Lifespan as FastAPI Lifespan
    participant Scheduler as Background Task (scheduler.py)
    participant CISA as US Gov CISA API
    participant DB as PostgreSQL (Locks & Storage)
    participant Service as EventService
    participant Repo as EventRepository

    Lifespan->>Scheduler: Start Task on App Boot (asyncio)
    
    loop Every 5 Minutes
        rect rgba(161, 146, 132, 1)
        Note over Scheduler,DB: Concurrency Control
        Scheduler->>DB: SELECT pg_try_advisory_lock(...)
        DB-->>Scheduler: Lock Acquired (Leader Node)
        end
        
        Scheduler->>CISA: HTTP GET /vulnerabilities.json (async httpx)
        CISA-->>Scheduler: Live JSON Threat Data
        Scheduler->>Service: bulk_ingest_events(events_data)
        
        rect rgba(173, 162, 185, 1)
        Note over Service,Repo: Algorithmic Deduplication
        Service->>Repo: get_existing_titles(incoming_titles)
        Repo->>DB: SELECT title FROM events WHERE title IN (...)
        DB-->>Repo: Existing Titles
        Repo-->>Service: Return Set of Existing Titles
        Service->>Service: Filter out duplicates, assign UUIDs to new
        end
        
        Service->>Repo: bulk_create(new_events)
        Repo->>DB: Bulk INSERT INTO events...
        DB-->>Repo: Success
        Repo-->>Service: Success
        Service-->>Scheduler: Returns number of ingested events
        
        Scheduler->>DB: SELECT pg_advisory_unlock(...)
        DB-->>Scheduler: Lock Released
    end
```

---

## 3. Stateless Authentication & Login Flow

This diagram illustrates the secure login process using bcrypt hashing and JSON Web Tokens (JWT). Notice that the database is only queried once during login; after that, the stateless JWT carries the proof of identity.

```mermaid
sequenceDiagram
    autonumber
    participant Browser as React Frontend
    participant Router as Auth Router (auth.py)
    participant Service as AuthService
    participant Repo as UserRepository
    participant DB as PostgreSQL

    Browser->>Router: POST /api/auth/login (email, password)
    Router->>Service: authenticate_user(email, password)
    
    rect rgba(149, 166, 184, 1)
    Note over Service,DB: Database Lookup
    Service->>Repo: get_by_email(email)
    Repo->>DB: SELECT * FROM users WHERE email = ...
    DB-->>Repo: User Row (including hashed password)
    Repo-->>Service: User Object
    end
    
    rect rgba(203, 192, 193, 1)
    Note over Service: Cryptographic Verification
    Service->>Service: bcrypt.verify(plain_password, hashed_password)
    end
    
    alt Password Matches
        Service->>Service: create_access_token(user_id)
        Service-->>Router: JWT String
        Router-->>Browser: JSON { "token": "ey..." } (200 OK)
        Browser->>Browser: Store JWT in localStorage
    else Password Fails
        Service-->>Router: Raise AuthError
        Router-->>Browser: 401 Unauthorized
    end
```

---

## 4. Automated CI/CD & AI Workflow (GitHub Actions)

This demonstrates the strict quality gates enforced by GitHub Actions and how AI (like myself) interacts with the repository securely.

```mermaid
sequenceDiagram
    autonumber
    participant Dev as AI Agent / Developer
    participant Git as Local Git
    participant GitHub as GitHub Repository
    participant Actions as GitHub Actions (CI)
    
    Dev->>Git: Write Code & Commit
    Dev->>Git: git push origin branch_name
    Git->>GitHub: Push Trigger
    
    rect rgba(223, 206, 206, 1)
    Note over GitHub,Actions: Automated Quality Gates
    GitHub->>Actions: Trigger CI Pipeline
    Actions->>Actions: Run ruff check (Linting)
    Actions->>Actions: Run mypy (Strict Typing)
    Actions->>Actions: Run ESLint (Frontend)
    Actions->>Actions: Run Pytest (Unit/Integration Tests)
    end
    
    alt All Tests Pass
        Actions-->>GitHub: ✅ Status Checks Passed
        GitHub-->>Dev: Branch is safe to merge
    else Any Test Fails
        Actions-->>GitHub: ❌ Status Checks Failed
        GitHub-->>Dev: Block Merge & Request Fixes
    end
```

---

## 5. Real-Time WebSocket Broadcasting Flow

This diagram illustrates how PostgreSQL acts as a brokerless pub/sub engine to synchronize multiple FastAPI workers and push live updates to the frontend React dashboard.

```mermaid
sequenceDiagram
    autonumber
    participant Browser as React Frontend
    participant WS as WebSocket Manager
    participant API as FastAPI Router / Scheduler
    participant Listener as Background Listener
    participant DB as PostgreSQL

    rect rgba(200, 206, 213, 1)
    Note over Browser,WS: Persistent Connection Setup
    Browser->>WS: Upgrade HTTP to ws://api/ws
    WS-->>Browser: Connection Established (101 Switching Protocols)
    end
    
    Listener->>DB: SQL: LISTEN new_events (Blocks & waits)
    
    rect rgba(194, 208, 194, 1)
    Note over API,DB: State Change Trigger
    API->>DB: INSERT / DELETE Event
    API->>DB: SQL: NOTIFY new_events, '{"type": "NEW_EVENTS"}'
    API->>DB: SQL: COMMIT
    end
    
    DB-->>Listener: Asynchronous Payload Received
    
    rect rgba(233, 206, 206, 1)
    Note over Listener,Browser: Cross-Worker Broadcast
    Listener->>WS: Broadcast Payload
    WS->>Browser: ws.send_json({"type": "NEW_EVENTS"})
    Browser->>Browser: React catches message, fetches fresh data
    end
```
