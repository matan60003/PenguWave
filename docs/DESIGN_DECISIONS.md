# PenguWave Design Decisions & Architecture

## 1. High-Level Architecture

The PenguWave platform follows a modern, asynchronous service-oriented architecture using a **Clean Architecture** layered approach. 

The backend is built with **FastAPI** (Python), exposing a RESTful API to the frontend and managing a continuous background telemetry ingestion pipeline. The application is divided into strict layers:
*   **Routers/Controllers**: Handle HTTP requests, routing, and security/JWT validation.
*   **Services**: Encapsulate the core business logic (e.g., algorithmic deduplication, password hashing).
*   **Repositories**: Abstract database interactions, preventing SQL leakage into business logic.
*   **Database**: A **PostgreSQL** relational database serves as the primary data store and distributed locking mechanism.

The frontend is a **React** application built with TypeScript, communicating with the backend via JSON payloads and securing sessions using stateless JWTs stored locally.

---

## 2. Technical Trade-offs

During development, several strategic decisions were made to balance performance, scalability, and operational simplicity:

*   **FastAPI for Async I/O**: 
    *   *Why*: I chose FastAPI over synchronous frameworks like Flask/Django because my workload involves heavily I/O-bound operations (fetching external CISA JSON feeds and performing bulk database inserts). Asynchronous execution allows the server to handle concurrent web requests while background tasks run simultaneously without blocking the main event loop.
*   **PostgreSQL Advisory Locks vs. Redis/Celery**: 
    *   *Why*: To prevent multiple worker nodes from running the same background telemetry ingestion task at once, I utilized `pg_try_advisory_lock`. While a dedicated message broker (like RabbitMQ) or cache (Redis) is the industry standard for distributed task queuing, utilizing PostgreSQL's native advisory locks allowed me to ensure concurrency control while keeping my infrastructure stack simple and reducing maintenance overhead for the project.
*   **UUID Primary Keys vs. Auto-Incrementing Integers**: 
    *   *Why*: I opted for UUIDs (e.g., `evt-uuid4()`) for database records instead of sequential IDs. While this creates a slightly larger database index, it entirely mitigates Insecure Direct Object Reference (IDOR) attacks by making IDs unguessable. Furthermore, it prepares the system for future horizontal database sharding.
*   **Stateless JWT Authentication vs. Server-Side Sessions**:
    *   *Why*: I chose JWTs to eliminate the need for a persistent session store (like Redis). This allows my backend workers to be completely stateless, meaning I can scale the API servers up and down effortlessly behind a load balancer.
*   **PostgreSQL (Relational) vs. NoSQL (MongoDB)**:
    *   *Why*: Security audit logs require absolute data integrity and rigid schemas. PostgreSQL provides transactional rollbacks to ensure failed bulk inserts don't corrupt the database, and it gives me powerful `.ilike()` text searching capabilities that are essential for filtering telemetry data.
*   **Server-Side Pagination vs. Client-Side Pagination**:
    *   *Why*: Fetching all events to paginate on the client would crash the browser's DOM if I ingested 100,000+ events. I use `.offset()` and `.limit()` in PostgreSQL so the backend guarantees the frontend only downloads the exact records required (e.g., 25 at a time), permanently capping memory usage.
*   **Database Indexing (B-Tree)**:
    *   *Why*: I applied B-Tree indexing to frequently searched columns like `userId` and `timestamp`. 
*   **Docker Containerization for Environment Parity**:
    *   *Why*: I orchestrated the React app, Python API, and PostgreSQL database using Docker. This ensures that the operating system dependencies are an exact 1:1 replica across local development and production, eliminating deployment failures caused by environment inconsistencies.
*   **Role-Based Access Control (RBAC) & Active Status Gates**:
    *   *Why*: I enforce strict RBAC at the dependency level in FastAPI and actively check user status against the database on every request. This ensures instantaneous revocation of access when an admin suspends a user, preventing privilege escalation.
*   **Pydantic for Data Validation**:
    *   *Why*: Pydantic intercepts JSON payloads before business logic executes, ensuring that my database only receives perfectly formatted data. This eliminates massive categories of bugs and vulnerabilities (like missing fields or incorrect types).
*   **React Context API vs. Redux**:
    *   *Why*: I opted for React Context API to manage global state (like Auth tokens). It provides a lightweight, highly efficient mechanism without the heavy boilerplate and dependency overhead of Redux.
*   **Frontend Exponential Backoff**:
    *   *Why*: Implementing a `fetchWithRetry` wrapper in React makes the platform incredibly resilient to minor network blips or temporary backend rate-limiting without abruptly crashing the user experience.
*   **XSS Mitigation via React Native Interpolation**:
    *   *Why*: I strictly avoid raw HTML injection (`dangerouslySetInnerHTML`) and rely on React's native string interpolation to sanitize inputs, rendering any injected scripts as plain text.

---

## 3. Implicit Assumptions

The current architecture operates under the following documented assumptions:

1.  **Expected Scale & Traffic**: I assume the initial platform will handle moderate read-heavy traffic (e.g., tens of thousands of requests per day) and low-volume write traffic (primarily the 5-minute background ingestion). PostgreSQL is assumed to be fully capable of handling both the application data and the distributed locking mechanism under this load.
2.  **Deployment Environment**: The system is assumed to be deployed in a containerized environment (like Docker/Kubernetes) where multiple instances of the backend container may be spun up automatically. This necessitated the distributed advisory lock to prevent data duplication.
3.  **Upstream Data Integrity**: I assume the external CISA KEV API provides a relatively consistent JSON schema, but I expect occasional missing data (such as dates), which is why graceful fallbacks to the current system time were implemented.
4.  **Network Transport Security**: I assume the application will be served strictly over HTTPS. Since I rely on JWTs passed in headers, executing this over plain HTTP would expose tokens to interception.

---

## 4. Future Scalability Improvements

If this system needed to scale to handle 100x the current traffic, I would evolve the architecture with the following steps:

1.  **Extract Background Tasks to Celery & Redis**: 
    Currently, the telemetry ingestion runs as an `asyncio` task inside the FastAPI lifespan. At 100x scale, long-running processing could degrade API performance. I would extract `scheduler.py` into standalone Celery worker nodes backed by a Redis queue, completely separating web traffic compute from background processing compute.
2.  **Implement Database Read Replicas**:
    As the dataset grows and users perform complex searches and filtering on events, the single PostgreSQL instance will become a bottleneck. I would implement a Primary-Replica database architecture, routing all `GET` requests to Read Replicas and all `POST/PUT/DELETE` requests (like the bulk ingestion) to the Primary node.
3.  **Introduce a Caching Layer**:
    The system currently queries PostgreSQL to deduplicate incoming vulnerabilities. At scale, this `IN (...)` query could become expensive. I would introduce Redis or Memcached to cache existing vulnerability titles and frequently accessed API responses, drastically reducing database read operations.
