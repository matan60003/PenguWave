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

## 🔐 How Security Works

### How Authentication Works
Authentication in PenguWave is completely **stateless**, utilizing JSON Web Tokens (JWT) and Bcrypt:
1. **Password Hashing:** When a user is created, their plaintext password is cryptographically hashed using `bcrypt` before being saved to PostgreSQL. We never store plaintext passwords.
2. **Login Verification:** Upon login, the backend verifies the provided password against the stored hash. If successful, it generates a JWT signed with a secret backend key.
3. **Stateless Sessions:** This token is returned to the React frontend, which stores it locally and attaches it to the `Authorization: Bearer <token>` header of every subsequent API request. The backend validates the cryptographic signature of the token to identify the user without needing to query a session database.

### How Authorization is Enforced
Authorization utilizes strict **Role-Based Access Control (RBAC)** across the stack:
1. **Backend Enforcement (The Source of Truth):** FastAPI dependencies (like `require_admin`) act as strict gates on the routing layer. If a standard user attempts to send a `DELETE /api/events/1` request, the backend actively inspects the role embedded in their JWT payload. If their role is not `admin`, the backend instantly rejects the request with a `403 Forbidden` error before any business logic executes.
2. **Active Status Checking:** Every protected request also queries the database to ensure the user's `status` is currently `active`. If an administrator suspends a user, their access is revoked instantly, even if their JWT hasn't expired yet.
3. **Frontend UX:** The React application reads the user's role and conditionally hides UI elements (like the "Delete" button or the "Users" admin panel) to prevent users from interacting with features they are not authorized to use.

---

## 🚀 How to Run the Project

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

---

## 🔒 How You Would Deploy This Securely In Production

To securely host this application on the internet, I would implement these fundamental security practices:

1.  **HTTPS (Encryption):** I would never run the app on basic HTTP. I would set up an SSL/TLS Certificate (using a reverse proxy like Nginx or AWS ALB) to ensure all traffic between the user's browser and the server is encrypted. Since we rely on JWTs passed in headers, HTTP would expose tokens to interception.
2.  **Environment Variables & Secrets:** I would remove all hardcoded passwords (like the database password in `docker-compose.yml`) and move them into hidden `.env` files or a cloud Secret Manager (like AWS Secrets Manager). These secrets would be injected into the containers at runtime and never committed to source control.
3.  **Database Network Isolation:** I would place the PostgreSQL database in a private subnet (VPC) that is completely inaccessible from the public internet. Only the FastAPI backend servers would have network access to talk to the database on port `5432`.
