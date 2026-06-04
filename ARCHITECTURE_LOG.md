# PenguWave Architecture Log 🛡️

This log records the technical impact, architectural decisions, and security justifications behind changes made during the development of the PenguWave backend.

---

## [2026-06-04] STEP-001: Dockerized Infrastructure Setup

### 🎯 Step Goal
Create the isolated backend service directory, define necessary dependencies, create a secure `Dockerfile` for the FastAPI server, and configure a `docker-compose.yml` to orchestrate the backend and a PostgreSQL database.

### 📁 Files Created/Modified
*   `[NEW]` [backend-service/requirements.txt](file:///c:/Users/matan/PenguWave/backend-service/requirements.txt) — Dependency specifications.
*   `[NEW]` [backend-service/Dockerfile](file:///c:/Users/matan/PenguWave/backend-service/Dockerfile) — Multi-stage, non-root runner build.
*   `[NEW]` [docker-compose.yml](file:///c:/Users/matan/PenguWave/docker-compose.yml) — Service orchestration.
*   `[MODIFY]` [progress.md](file:///c:/Users/matan/PenguWave/progress.md) — Progress tracking updates.
*   `[MODIFY]` [.antigravity/rules/aidd-workflow.mdc](file:///c:/Users/matan/PenguWave/.antigravity/rules/aidd-workflow.mdc) — Commit and documentation rules.

### 🏗️ Architectural Decisions & "Why"

#### 1. Codebase Isolation
*   **Decision:** Place all backend resources inside a dedicated `backend-service/` directory rather than the root or a generic `backend/` folder.
*   **Why:** Completely decouples backend logic from frontend build tools (Vite, ESLint, TypeScript node setups). This allows distinct packaging, containerization, and independent microservice deployment pathways in CI/CD pipelines.

#### 2. Multi-Stage Docker Build
*   **Decision:** Used a two-stage Docker build (`builder` -> `runner`) using `python:3.11-slim` as the base image.
*   **Why (Security & Optimization):** 
    *   *Reduced Attack Surface:* The builder stage compiles C extensions and downloads packages using build utilities (`gcc`, `libpq-dev`). The final runner image copies only the built packages and application code, omitting build compilers. This denies potential attackers access to native compiler tools if the container is compromised.
    *   *Image Size Reduction:* Eliminating build-time dependencies drastically reduces the runner image footprint.

#### 3. Principle of Least Privilege (Non-Root Execution)
*   **Decision:** Created a system group and user (`appuser`) with a disabled shell (`/sbin/nologin`) and configured the container to run under this user (`USER appuser`).
*   **Why (Security):** Containers running as `root` pose a severe kernel-escape risk. If an application dependency suffers an RCE (Remote Code Execution) exploit, the attacker gains root privilege within the container, which can lead to host filesystem takeover. Running as `appuser` mitigates this risk.

#### 4. PostgreSQL Network Isolation
*   **Decision:** Did not map host ports to the database container in `docker-compose.yml` (no `ports: - "5432:5432"` configuration).
*   **Why (Security):** The database is only accessible to containers on the same Docker-managed network. The backend connects directly via the container's DNS alias `db:5432`. By not exposing port 5432 to the host network interface, we protect the database from external internet-based brute-force or scanning attempts.

#### 5. Database Persistence
*   **Decision:** Configured a named volume `db_data` mapping the database storage directory.
*   **Why (Resilience):** Container filesystems are ephemeral. Persisting PostgreSQL data to a host-managed volume guarantees that event logs and user credentials survive container updates, restarts, and deletions.

#### 6. Database Healthcheck Dependency Mapping
*   **Decision:** Configured a healthcheck on the database using `pg_isready` and mapped the backend container's start condition to `service_healthy`.
*   **Why (Resilience):** Prevents the FastAPI server from starting and crashing during database initialization phases, ensuring a clean and automated bootstrap sequence.

#### 7. Essential Security & Config Dependency Locking
*   **Decision:** Locked in dependencies for `pydantic-settings` (secure config parsing), `passlib[bcrypt]` (industry-standard key-stretched hashing for password protection), and `pyjwt` (stateless authorization).

---

## [2026-06-04] Addendum: GitHub Actions CI Quality Gates

### 🎯 Step Goal
Configure a continuous integration workflow running static checks, type validation, and automated security scans to enforce quality gates on every Pull Request to `main`.

### 📁 Files Created/Modified
*   `[NEW]` [.github/workflows/ci.yml](file:///c:/Users/matan/PenguWave/.github/workflows/ci.yml) — GitHub Actions workflow configuration.
*   `[NEW]` [backend-service/main.py](file:///c:/Users/matan/PenguWave/backend-service/main.py) — Baseline FastAPI app entrypoint.
*   `[MODIFY]` [backend-service/requirements.txt](file:///c:/Users/matan/PenguWave/backend-service/requirements.txt) — Security patch updates.
*   `[MODIFY]` [ARCHITECTURE_LOG.md](file:///c:/Users/matan/PenguWave/ARCHITECTURE_LOG.md) — Documentation updates.

### 🏗️ Architectural Decisions & "Why"

#### 1. Shift-Left Security Scans
*   **Decision:** Integrated SAST (Static Application Security Testing) via `bandit` and SCA (Software Composition Analysis) via `pip-audit` directly into the CI pipeline.
*   **Why (Security):** 
    *   `bandit` automatically flags code patterns (like hardcoded keys, debug flags, or shell injections) that could introduce vulnerabilities before they hit production.
    *   `pip-audit` cross-references our pinned dependency versions against the PyPA advisory database, blocking merging of any packages with known active vulnerabilities (Supply Chain Security).

#### 2. Automated Type-Safety Checks
*   **Decision:** Configured `mypy` static type analyzer to run on `backend-service/`.
*   **Why (Quality):** FastAPI relies on Python type annotations for serialization and data validation. Catching type mismatches at PR-time prevents data parsing failures and runtime crashes. We use `--ignore-missing-imports` to avoid build failure on library stubs that are not natively type-hinted.

#### 3. Linting and Formatting Check
*   **Decision:** Utilized `ruff` for both code style checking and lint enforcement.
*   **Why (Efficiency):** `ruff` replaces multiple Python lint tools and runs extremely fast, keeping developer feedback loops tight and maintaining clean, standardized formatting across the codebase.

#### 4. Baseline Scaffolding for Quality Gates
*   **Decision:** Initialized a basic `main.py` containing a `/healthz` check endpoint rather than bypassing or silencing Mypy compiler checks.
*   **Why:** Rather than muting checks (which hides potential bugs) or postponing type enforcement, scaffolding the entrypoint file immediately satisfies the compiler. The `/healthz` endpoint serves as a standard readiness probe for containerized environments.

#### 5. SCA Vulnerability Patching
*   **Decision:** Upgraded `pyjwt` to `2.13.0` and `fastapi` to `0.115.8` (which transitively upgrades the underlying `starlette` dependency to `0.45.3`).
*   **Why (Security):** Older versions of `pyjwt` and `starlette` contain critical security vulnerabilities (e.g. signature verification bypasses and DoS opportunities). Upgrading them remediates all reported vulnerabilities, securing our authentication mechanics and HTTP routing pipeline.



