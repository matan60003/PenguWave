# PenguWave System Architecture

This document outlines the core architectural components of the PenguWave Analyst Platform. It details the structural boundaries between our services, our approach to resilient data engineering, observability, and robust security.

## 1. Database Tier & ORM Layer Evolution

The data tier has been modernized from ephemeral mock structures to a robust, containerized **PostgreSQL** database layer. This ensures durable persistence and high availability for the analytical platform.

**SQLAlchemy Integration:**
- **ORM Mapping:** We utilize SQLAlchemy as our primary Object-Relational Mapper (ORM), abstracting low-level SQL syntax into strongly typed Python representations (e.g., `Event`, `User`).
- **Session Lifecycle & Middleware:** The database session is bound to the request lifecycle via the `get_db` FastAPI dependency generator. This dependency guarantees deterministic connection disposal.
- **Safety Rollback Strategies:** A resilient exception-handling layer within the dependency explicitly invokes `db.rollback()` upon encountering any unhandled engine exceptions. This prevents dirty transactions from leaking back into the pool, averting catastrophic memory leaks and pool exhaustion.
- **Relational Optimization:** To support sub-second backend analytical querying, we employ aggressive indexing. Most notably, a multi-tenant search index was deployed on `Event.userId`, ensuring fast lookup speeds when querying large event volumes across multiple users.

## 2. System Auditing & Observability Framework

Ensuring the platform remains auditable and transparent requires rigorous observability tooling.

**Structured Logging:**
- A custom `JSONLogFormatter` is embedded deeply within the FastAPI initialization loop (`app/main.py`). This guarantees all log outputs stream as highly structured JSON objects, making them instantly ingestible by downstream observability platforms (e.g., ELK or Datadog) without convoluted regex parsing.

**Explicit Exception Handling Hierarchy:**
- Rather than leaking raw Python stack traces directly to the client, the backend architecture intercepts complex runtime errors via an explicit exception handling hierarchy.
- Exceptions like `OperationalError` (DB faults), `ValidationError` (Pydantic mismatches), and `PyJWTError` (Token failures) are caught globally.
- These are securely audited locally to the application logs (`app.log`) and subsequently sanitized into predictable, RFC-compliant HTTP status codes (503, 422, and 401).

## 3. Security, Auth, & RBAC Specification

PenguWave utilizes a stateless JSON Web Token (JWT) architecture to orchestrate Role-Based Access Control (RBAC).

**Unified JWT Decoding Pipeline:**
- Incoming API requests traverse a stringent authentication dependency (`get_current_user`). 
- The JWT is cryptographically verified to ensure structural integrity and signature validity.
- **Dynamic Status Validation:** Merely possessing a structurally valid, unexpired token is insufficient. The authorization pipeline executes a strict `user.status == "active"` check against the persistent database. This effectively mitigates critical authorization bypass vulnerabilities, ensuring that if a user profile is deactivated or suspended in the system, their active sessions are instantaneously revoked.

## 4. Frontend Architecture & Resiliency Engineering

The frontend application (React/Vite) is constructed to withstand transient infrastructure blips and aggressively sanitize rendering vectors.

**Client-Side API Orchestration:**
- API interactions are centralized within `src/api.ts`.
- **Exponential Backoff Retry Strategy:** The orchestration layer leverages a custom `fetchWithRetry` wrapper. This implements an automated HTTP exponential backoff architecture. Should the upstream API gateway encounter transient timeouts or short-lived service degradation, the client transparently retries the request, seamlessly isolating the user session from underlying infrastructure flutter.

**XSS Remediation & DOM Sanitization:**
- High-risk Cross-Site Scripting (XSS) rendering vulnerabilities have been eradicated within the analytical event log dashboard (`EventsPage.tsx`).
- Rather than bypassing React’s synthetic event structure via `dangerouslySetInnerHTML`, user-supplied search queries are safely sanitized and interpolated natively within the React DOM, providing a bulletproof defense against injection payloads.
