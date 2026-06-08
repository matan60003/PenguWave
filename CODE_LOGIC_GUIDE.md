# PenguWave Code Logic & Developer Guide

This guide is designed to help developers read, understand, and navigate the core logic of the PenguWave codebase. Instead of high-level architecture, this focuses on **how the code actually works**, highlighting the most important functions and logical flows.

---

## 1. Authentication & Security Logic
*Where it lives:* `**`create_access_token(data: dict)`**: Located in `security.py`. When a user successfully logs in, this function takes their user ID, adds an expiration time (`exp`), and signs it cryptographically using our `SECRET_KEY`. This outputs the JWT string.
*   **`get_current_user(token: str = Depends(oauth2_scheme))`**: Located in `dependencies.py`. This is our most critical security gate. Every protected API route calls this function first. 
    *   **The Logic:** It intercepts the incoming HTTP request, extracts the JWT from the `Authorization` header, and decodes it. If the token is expired or altered, it throws a `401 Unauthorized` error. If valid, it fetches the user from the database and returns the User object so the API knows exactly who is making the request.

---

## 2. Database Services & Clean Architecture
*Where it lives:* `backend-service/app/services/` & `backend-service/app/database/repositories.py`

### Important Functions & Patterns:
*   **The Repository Pattern (`UserRepository`, `EventRepository`)**: 
    *   **The Logic:** Instead of service logic querying `await db.execute(select(models.User))` directly, it delegates to a repository interface. This abstracts raw SQLAlchemy commands away from the business layer.
*   **Dependency Injection (`AuthService`, `UserService`, `EventService`)**: 
    *   **The Logic:** `auth_service.py` exports an `AuthService` class initialized with dependencies (like `UserRepository`). The FastAPI router dynamically constructs and injects these services into endpoints using `Depends()`. This ensures the router only handles HTTP requests, while the service handles the algorithms and returns strict Pydantic schemas.
*   **`get_events(severity, search, limit, offset)` in `EventRepository`**: This is the heart of our **Server-Side Pagination**.
    *   **The Logic:** Instead of just returning all events, it starts with a base query (`select(models.Event)`). 
    *   If a `search` string is provided, it modifies the query to check if the title, description, or asset matches using SQLAlchemy's `.ilike()` (case-insensitive search).
    *   It calculates the `total` number of matching rows using a separate `select(func.count())` execution.
    *   Finally, it applies the `.offset(offset).limit(limit)` logic to slice out exactly 25 rows and executes it via `await self.db.execute()`, preventing our database from sending massive payloads.

---

## 3. Background Task & Telemetry Ingestion
*Where it lives:* `backend-service/app/core/scheduler.py` & `backend-service/app/core/lifespan.py`

### Important Functions:
*   **`lifespan(app: FastAPI)`**: Located in `lifespan.py`.
    *   **The Logic:** This is FastAPI's startup/shutdown hook. When you run `docker-compose up`, this function executes. It first boots up the database schema (`Base.metadata.create_all`). Then, critically, it triggers `asyncio.create_task(heartbeat_task())`. This tells Python to run our scheduler in the background without freezing the web server.
*   **`_fetch_and_ingest_cisa_data()`**: Located in `scheduler.py`.
    *   **The Logic:** This function pings the US Government's CISA API using an asynchronous HTTP client (`httpx`). When the JSON data returns, it loops through the vulnerabilities. 
    *   **Deduplication Logic:** Before saving, it extracts all incoming vulnerability titles and runs a single batch query: `await db.execute(select(models.Event.title).filter(models.Event.title.in_(titles)))`. If it finds a match in the resulting set, it skips it (`continue`). This ensures we don't accidentally insert the same vulnerability twice every 5 minutes while avoiding severe N+1 database bottlenecks.

---

## 4. Frontend Network & Retry Logic
*Where it lives:* `frontend/src/api.ts`

### Important Function:
*   **`fetchWithRetry(url, options, retries, backoff)`**: This powers every single API request in the React app.
    *   **The Logic:** Networks are unreliable. If the backend is restarting or temporarily dropping packets, a normal `fetch()` would instantly crash the React app and show a red error. This function wraps `fetch()` in a `for` loop. If it detects a `500 Server Error` or network failure, it uses **Exponential Backoff**: it waits 300ms, tries again, then waits 600ms, then 1200ms. If it hits a `4xx Client Error` (like a 401 Unauthorized), it knows it's the user's fault and correctly stops retrying to prompt a login.

---

## 5. Frontend State Management & UI Rendering
*Where it lives:* `frontend/src/pages/EventsPage.tsx`

### Important Logic (React Hooks):
*   **The `useEffect` Dependency Array**: 
    ```tsx
    useEffect(() => {
      // Fetches data
    }, [page, search, severityFilter]);
    ```
    *   **The Logic:** This is the core of React's reactivity. Whenever the variables inside the array (`page`, `search`, `severityFilter`) change, React automatically re-runs the code block inside the `useEffect`. 
    *   So, when a user clicks the "Next Page" button, `setPage(page + 1)` fires. The `page` variable changes. React sees the change, instantly triggers the `useEffect`, and calls `getEvents()` with the new page number, seamlessly updating the table without a page refresh!
