# PenguWave Codebase Dictionary

This document provides a highly detailed, comprehensive breakdown of every major folder and file in the PenguWave codebase. It includes explanations of technical terms, architectural decisions, and specific code examples directly from the source files.

---

## 🏗️ Root Directory

The root directory contains the core configuration files, orchestration tools, and architectural documentation for the entire project.

### `docker-compose.yml`
*   **What it is:** An orchestration file for Docker.
*   **Technical Concept:** **Container Orchestration**. It defines how multiple isolated containers (the PostgreSQL database and the FastAPI backend server) interact, share networks, and mount volumes.
*   **Code Example:**
    ```yaml
    services:
      db:
        image: postgres:15
        environment:
          POSTGRES_DB: penguwave
      backend:
        build: ./backend-service
        depends_on:
          - db
    ```

### `README.md`, `ARCHITECTURE.md`, `SYSTEM_DESIGN_SPEC.md`, `CODE_LOGIC_GUIDE.md`
*   **What they are:** Markdown documentation files detailing how to run the project, architectural decisions, system flows, and core algorithmic logic.

---

## 🐍 `backend-service/` (FastAPI Server)

This directory contains the Python-based FastAPI backend, utilizing a decoupled, "Clean Architecture" design pattern.

### `Dockerfile`
*   **What it is:** The instruction manual for building the backend Docker image. It installs Python, copies `requirements.txt`, installs dependencies, and specifies the startup command (`uvicorn`).

### `app/main.py`
*   **What it is:** The primary entry point for the FastAPI application.
*   **Technical Concept:** **Middleware & Exception Handling**. It configures CORS (Cross-Origin Resource Sharing) to allow the frontend to communicate with it, sets up the application lifespan, and binds global exception handlers to format error responses.
*   **Code Example:**
    ```python
    # Binds the lifespan (background tasks) and initializes the app
    app = FastAPI(
        title="PenguWave API",
        lifespan=lifespan,
    )

    # Catches JWT token errors globally and returns a clean 401 Unauthorized
    @app.exception_handler(jwt.exceptions.PyJWTError)
    async def jwt_exception_handler(request, exc: jwt.exceptions.PyJWTError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid authentication token"},
        )
    ```

---

### 🔀 `app/api/` (Routing Layer)

This folder strictly handles HTTP request routing, path parameters, and dependency injection. It contains **no** business logic or database queries.

#### `events.py`, `users.py`, `auth.py`
*   **What they are:** API routers for specific domain entities.
*   **Technical Concept:** **Dependency Injection (DI)**. The routers rely on FastAPI's `Depends()` to dynamically inject service classes and authentication gates before running the endpoint logic.

#### `dependencies.py`
*   **What it is:** Contains shared dependencies injected into the routers, such as token validation.
*   **Technical Concept:** **Stateless Authentication Gate**. The `get_current_user` function extracts the JWT, verifies its cryptographic signature, and fetches the user object, ensuring only authorized users reach protected endpoints.

---

### ⚙️ `app/core/` (System Core)

Contains system-level configurations, background task logic, and security algorithms.

#### `lifespan.py`
*   **What it is:** Handles the startup and shutdown sequence of the web server.
*   **Technical Concept:** **Native Asyncio Tasks**. Instead of using heavy external workers like Celery, it ties a background task directly to the asynchronous event loop.

#### `scheduler.py`
*   **What it is:** Runs the background telemetry engine.
*   **Technical Concept:** **Distributed Advisory Locks**. Before fetching CISA threat data, it locks the database session to ensure only one worker process performs the ingestion at a time, preventing race conditions.

#### `security.py`
*   **What it is:** Contains cryptographic functions for hashing passwords and signing JWTs.
*   **Technical Concept:** **Bcrypt Hashing**. Converts plaintext passwords into irreversible hashes.

#### `exceptions.py` & `config.py`
*   **What they are:** `config.py` loads environment variables safely. `exceptions.py` defines custom domain exceptions (e.g., `NotFoundError`) so the service layer can raise errors without knowing about HTTP status codes.

---

### 💾 `app/database/` (Data Access Layer)

Manages all interactions with the PostgreSQL database.

#### `database.py`
*   **What it is:** Configures the SQLAlchemy asynchronous engine and session maker.

#### `models.py`
*   **What it is:** Defines the SQL table structures using Object-Relational Mapping (ORM).
*   **Technical Concept:** **UUID Primary Keys & B-Tree Indexing**. Uses random UUIDs instead of sequential integers for security, and adds indexes for lightning-fast queries.
*   **Code Example:**
    ```python
    class Event(Base):
        __tablename__ = "events"
        # Uses UUIDs and creates an index for faster lookups
        id: Mapped[str] = mapped_column(String, primary_key=True, index=True) 
        title: Mapped[str] = mapped_column(String, nullable=False)
    ```

#### `repositories.py`
*   **What it is:** Implements the **Repository Pattern**. It abstracts raw SQL/SQLAlchemy queries away from the business logic.
*   **Technical Concept:** **Server-Side Pagination**. The `EventRepository` handles massive datasets by applying `.limit()` and `.offset()` directly in the database, so the server never loads a million rows into memory at once.

---

### 🛡️ `app/schemas/` (Validation Layer)

#### `schemas.py`
*   **What it is:** Uses the Pydantic library to define the exact shape of incoming JSON requests and outgoing responses.
*   **Technical Concept:** **Strict Data Validation**. If the frontend sends an invalid email format or a string instead of a boolean, Pydantic immediately rejects the request with a `422 Unprocessable Entity` before it ever reaches the routers.

---

### 🧠 `app/services/` (Business Logic Layer)

#### `auth_service.py`, `event_service.py`, `user_service.py`
*   **What they are:** The "brain" of the application. They contain the actual algorithmic work, such as verifying credentials or orchestrating bulk data ingestion, completely decoupled from HTTP frameworks.

---

## ⚛️ `frontend/` (React SPA)

The frontend is a Single Page Application (SPA) built with React, TypeScript, and Vite.

### `package.json`, `vite.config.ts`, `tsconfig.json`
*   **What they are:** Build tools and configuration files. `vite.config.ts` handles the blazing-fast development server, while `tsconfig.json` enforces strict static typing.

### `src/main.tsx` & `src/App.tsx`
*   **What they are:** The root mounting points for the React component tree. `App.tsx` configures the frontend router (e.g., mapping the `/events` URL to the `EventsPage` component).

### `src/api.ts`
*   **What it is:** The centralized network client for communicating with the backend.
*   **Technical Concept:** **Exponential Backoff Wrapper**. It wraps standard `fetch()` calls in a resilient retry loop. If the backend restarts, it waits and retries automatically instead of crashing the UI.
*   **Code Example:**
    ```typescript
    export async function getEvents(page = 1, limit = 25, search = "") {
      const offset = (page - 1) * limit;
      const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
      if (search) params.append("search", search);
      // Calls the exponential backoff wrapper
      return fetchWithRetry(`${API_URL}/api/events?${params.toString()}`);
    }
    ```

### `src/context/AuthContext.tsx`
*   **What it is:** Manages global authentication state.
*   **Technical Concept:** **React Context API**. Instead of passing the logged-in user's data down through every single component manually (prop drilling), it stores the JWT and user profile globally so any component (like a Navbar) can instantly access it.
*   **Code Example:**
    ```tsx
    // Fetches the user profile silently when the app loads if a token exists
    useEffect(() => {
      const initializeAuth = async () => {
        if (token) {
          const userData = await getCurrentUser();
          setUser(userData);
        }
        setLoading(false);
      };
      initializeAuth();
    }, [token]);
    ```

### `src/pages/`
*   **What they are:** The primary full-screen views (e.g., `EventsPage.tsx`, `LoginPage.tsx`, `UsersPage.tsx`).
*   **Technical Concept:** **Reactivity**. They use `useState` and `useEffect` hooks. When a user clicks "Next Page", the state updates, triggering an automatic API fetch and re-rendering the table seamlessly.

### `src/components/`
*   **What they are:** Smaller, reusable building blocks like `Navbar.tsx`, `CreateEventModal.tsx`, and `ProtectedRoute.tsx`.
*   **Technical Concept:** **Component Isolation**. By breaking the UI into smaller parts, the code remains highly readable and maintainable. `ProtectedRoute.tsx` wraps around sensitive pages and forces a redirect to the login screen if no valid JWT is found.

### `src/types.ts`
*   **What it is:** Defines strict TypeScript interfaces (e.g., `interface Event { id: string; title: string; }`). This ensures the frontend exactly expects the JSON shape provided by the backend Pydantic schemas.

---

## 📂 `data/`

### `mock_events.json`
*   **What it is:** A JSON file containing initial seed data. During the very first database boot, the system parses this file to populate the `events` table so developers immediately have data to test with.

---

## 🔬 Core Functions & Critical Flows

Beyond the file structure, here are the most significant functions driving PenguWave's core capabilities.

### `_fetch_and_ingest_cisa_data()` (Background Telemetry)
*   **Location:** `app/core/scheduler.py`
*   **What it does:** This is the heart of the automated threat intelligence system. It runs every 5 minutes in the background, fetches live JSON data from the US Government's CISA feed, maps it to our internal `EventCreate` schema, and passes it to the `EventService` for ingestion.
*   **Significant Concept:** **Distributed Advisory Locks**. Before making the network request, it executes `SELECT pg_try_advisory_lock(...)`. If multiple servers are running, only one server will successfully acquire this lock, preventing duplicate requests and API throttling.
*   **Code Example:**
    ```python
    # Try to acquire an advisory lock to prevent multiple workers from running this simultaneously
    result = await lock_db.execute(text("SELECT pg_try_advisory_lock(1029384756)"))
    lock_acquired = result.scalar()
    if not lock_acquired:
        logger.debug("Another worker is running the CISA fetch. Skipping.")
        return
    ```

### `bulk_ingest_events()` (Data Deduplication)
*   **Location:** `app/services/event_service.py`
*   **What it does:** Takes a list of raw event payloads from the scheduler and safely saves them to the database.
*   **Significant Concept:** **Algorithmic Deduplication**. Instead of inserting data blindly or running an expensive SQL query for every single event, it grabs all incoming titles, runs a single chunked `IN()` query to find existing duplicates in the database, and only assigns UUIDs to the truly new events.

### `get_current_user()` (Stateless Authentication Gate)
*   **Location:** `app/api/dependencies.py`
*   **What it does:** This is the absolute core of the backend security model. Any API endpoint that requires the user to be logged in will call this function first.
*   **Significant Concept:** **Active Status Gating**. It decodes the JWT, verifies the cryptographic signature, and explicitly queries the database to ensure the user's status is still "active". If an admin suspends a user, this function will instantly throw a `403 FORBIDDEN` error on their next click, overriding the fact that their JWT hasn't expired yet.
*   **Code Example:**
    ```python
    user = await user_repo.get_by_id(user_id)
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    ```

### `fetchWithRetry()` (Frontend Network Resiliency)
*   **Location:** `frontend/src/api.ts`
*   **What it does:** A custom wrapper around the standard browser `fetch()` API that handles all network communication with the backend.
*   **Significant Concept:** **Exponential Backoff**. If the backend server drops a connection or returns a 500 error, this function doesn't crash the React app. Instead, it catches the error and waits (`setTimeout`) for 300ms, then 600ms, then 1200ms before retrying, making the UI highly fault-tolerant.
*   **Code Example:**
    ```typescript
    } catch (err) {
      if (i === retries) throw err;
      // Exponential backoff: waits longer after each failure
      await new Promise(resolve => setTimeout(resolve, backoff * Math.pow(2, i)));
    }
    ```
