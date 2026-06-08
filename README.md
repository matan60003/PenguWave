# PenguWave: Security Operations Portal

PenguWave is a production-grade, full-stack Security Operations Portal designed for analyzing and monitoring security events, user activity, and threat intelligence telemetry across your infrastructure.

---

## 🏗️ Architecture

PenguWave operates as a decoupled monolith built for high concurrency and robust security.

*   **Frontend:** React (TypeScript) powered by Vite. Uses custom Context API for stateless JWT session management and an exponential backoff network layer for extreme UI resilience.
*   **Backend:** FastAPI (Python) utilizing native `asyncio`. Chosen for its unmatched I/O performance which is critical for real-time telemetry processing.
*   **Database:** PostgreSQL, accessed via SQLAlchemy ORM. Provides strict ACID compliance, relational integrity, and indexing (B-Tree) for fast queries.
*   **Data Validation:** Pydantic strictly validates all incoming requests and outgoing API responses, ensuring absolute data conformity.
*   **Containerization:** The backend server and PostgreSQL database are fully containerized using Docker and orchestrated via `docker-compose`.

## 🔌 External APIs Used
*   **CISA KEV Feed:** PenguWave operates a background scheduler that routinely pings the US Government's **Known Exploited Vulnerabilities (KEV)** API (`https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`) to automatically ingest live threat intelligence into the dashboard.

## ✨ Implemented Features

1.  **JWT Authentication & RBAC:** Secure, stateless login system. Users possess specific roles (`admin` vs `user`), and the backend strictly enforces permissions (e.g., only admins can delete events or create users). Passwords are cryptographically hashed using `bcrypt`.
2.  **Server-Side Pagination & Search:** The Events dashboard is designed to scale infinitely. Instead of loading millions of rows into the browser, the backend uses SQLAlchemy `.limit()`, `.offset()`, and `.ilike()` operators to retrieve exactly 25 rows at a time and filter searches directly in PostgreSQL.
3.  **Real-Time Background Telemetry Engine:** A native `asyncio` task runs silently inside the FastAPI event loop, routinely fetching data from the CISA API, running deduplication checks, and inserting new vulnerabilities into the database without blocking the main web server.
4.  **Resilient Network Layer:** The frontend uses an exponential backoff wrapper around `fetch()`. If the backend temporarily drops a connection or restarts, the frontend silently retries with increasing delays, preventing sudden application crashes.
5.  **Distributed Task Locking:** Uses PostgreSQL Advisory Locks to guarantee the background scheduler only runs once per cycle, even if the FastAPI backend is horizontally scaled across multiple worker processes.

## ⚠️ Known Limitations

1.  **Simulated Telemetry Fields:** Because the CISA KEV API only provides vulnerability descriptions and CVE IDs, our ingestion script currently generates "mock" data for the `sourceIp`, `assetHostname`, and `tags` fields to simulate a realistic network intrusion event.

---

## 🚀 How to Run the System

### Prerequisites
*   [Docker](https://docs.docker.com/get-docker/) & Docker Compose installed.
*   [Node.js](https://nodejs.org/) v18+ installed.

### 1. Start the Backend & Database (Docker)
Open a terminal in the root directory and start the Docker containers:
```bash
docker-compose up --build -d
```
*   The PostgreSQL database will initialize on port `5432`.
*   The FastAPI backend will run on `http://localhost:3001`.
*   *Note: Upon first boot, the system automatically runs schema migrations and seeds the database with default data and a mock events JSON file.*

### 2. Start the Frontend (Localhost)
Open a second terminal, navigate to the frontend directory, install the dependencies, and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
*   The React app will be available at `http://localhost:5173`.

### 3. Login Credentials
Once the frontend loads, use the seeded admin credentials to log in:
*   **Email:** `admin@penguwave.com`
*   **Password:** `adminpassword`
