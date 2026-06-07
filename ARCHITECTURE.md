# PenguWave System Architecture & Technology Guide

This document serves as your ultimate technical guide and dictionary for the PenguWave Full-Stack Security Operations Portal. It breaks down every major technology we used across the stack, explaining **what** it is, **why** we use it, and **how** it works in our system.

---

## 1. Authentication (Proving Who You Are)

Authentication is the process of verifying a user's identity (e.g., logging in with an email and password).

- **JSON Web Tokens (JWT):**
  - **What it is:** A secure, digitally signed string of text that acts like a digital ID card.
  - **How we use it:** When you log in, the server generates a JWT containing your user ID and role, and cryptographically signs it using a secret key. This token is sent to the frontend React app. The frontend then attaches this token to the header of every subsequent API request to prove who is making the request without needing to send the password every time. 
  - **Why it matters:** It makes our system "stateless." The backend doesn't need to remember who is logged in because the token itself carries all the necessary proof, allowing the server to handle thousands of requests seamlessly.

- **Bcrypt Hashing:**
  - **What it is:** A cryptographic algorithm designed specifically for safely storing passwords.
  - **How we use it:** We never store plaintext passwords in our database. When a user is created, `bcrypt` scrambles their password into an irreversible hash. When they log in, `bcrypt` hashes the password they typed and compares it to the stored hash to see if they match.
  - **Why it matters:** If an attacker ever breached the database, they would only see scrambled text, meaning your users' actual passwords remain highly secure.

---

## 2. Authorization (Controlling What You Can Do)

Authorization happens *after* Authentication. It determines what a logged-in user is allowed to access or change.

- **Role-Based Access Control (RBAC):**
  - **What it is:** A security paradigm where permissions are granted based on a user's assigned "Role" (e.g., `admin`, `analyst`).
  - **How we use it:** Our frontend (`UsersPage.tsx`, `EventsPage.tsx`) checks your role to decide whether to hide or show buttons like "Delete Event" or "Create User." Simultaneously, our backend API endpoints (like `create_user`) use a "dependency" (`require_admin`) that strictly checks your JWT token. If an `analyst` tries to call an admin-only endpoint, the backend forcefully rejects it with a `403 Forbidden` error.
  - **Why it matters:** It prevents privilege escalation. Even if a clever user unhides the "Delete" button in their browser using developer tools, the backend will still block the action because it verifies their role independently.

- **Active Status Gates:**
  - **What it is:** A database-level check to ensure a user account hasn't been disabled.
  - **How we use it:** Even if a user has a valid, unexpired JWT token, our backend authentication pipeline always queries the database to ensure `user.status == "active"`. If an admin suspends a user, their access is instantly revoked on their very next click.

---

## 3. Backend API (The Engine)

The Backend API is the server that processes business logic, talks to the database, and serves data to the frontend.

- **FastAPI (Python):**
  - **What it is:** A modern, high-performance web framework for building APIs with Python.
  - **How we use it:** It serves as our core application router. It listens for HTTP requests from the React frontend (like `GET /api/events`), runs the Python code to fetch the data, and returns it as JSON.
  - **Why it matters:** FastAPI uses asynchronous programming (`async`/`await`), meaning it can handle many concurrent requests extremely fast without slowing down. It also automatically generates interactive documentation (Swagger UI), making it easy to test our endpoints.

- **Pydantic (Data Validation):**
  - **What it is:** A Python library for data parsing and validation.
  - **How we use it:** Before FastAPI runs our logic, Pydantic intercepts the incoming JSON request (e.g., when creating an event) and ensures it perfectly matches our defined schemas. If an admin forgets to send a `timestamp` or sends a number instead of a string, Pydantic blocks it and returns a highly detailed `422 Unprocessable Entity` error.
  - **Why it matters:** It guarantees that our database only receives perfectly formatted data, completely eliminating a massive category of bugs and security vulnerabilities.

---

## 4. Storage (The Brain)

This is where all of our permanent data lives.

- **PostgreSQL:**
  - **What it is:** A powerful, open-source relational database management system.
  - **How we use it:** We store our `Users` and `Events` in strict, tabular structures (tables with rows and columns).
  - **Why it matters:** It provides strict ACID compliance (Atomicity, Consistency, Isolation, Durability), meaning that even if the server crashes in the middle of saving an event, the data will never be left in a corrupted or half-written state.

- **SQLAlchemy (ORM):**
  - **What it is:** An Object-Relational Mapper for Python.
  - **How we use it:** Instead of writing raw SQL strings like `SELECT * FROM events`, SQLAlchemy allows us to interact with the database using standard Python objects. When we want to save a new event, we just create a Python `Event` class instance and call `db.add()`.
  - **Why it matters:** It makes the code vastly cleaner, safer from SQL Injection attacks, and much easier to maintain. We also implemented strict "Rollback" strategies, meaning if an error happens during a database operation, SQLAlchemy cleanly reverts the changes so the database connection isn't broken.

---

## 5. Events Data (The Telemetry)

This relates to how we handle the core security event logs inside our system.

- **UUIDs (Universally Unique Identifiers):**
  - **What it is:** A 36-character string of random letters and numbers used as a unique ID (e.g., `evt-a1b2c3d4...`).
  - **How we use it:** Instead of using sequential numbers (1, 2, 3) for our event and user IDs, we generate a random UUID for every new record.
  - **Why it matters:** Using sequential IDs allows attackers to easily guess how many events exist or scrape data by simply counting up (e.g., trying to fetch `/events/5`, `/events/6`). UUIDs make the IDs completely unguessable.

- **Multi-Tenant Indexing:**
  - **What it is:** A database optimization technique.
  - **How we use it:** We created a B-Tree index on `Event.userId` in the PostgreSQL database.
  - **Why it matters:** As the system scales to millions of events, searching for one specific user's events could take seconds. By indexing the column, PostgreSQL maintains an organized lookup tree, allowing it to find records in milliseconds, keeping the UI lightning fast.

- **Server-Side Pagination & Database Filtering:**
  - **What it is:** The process of breaking massive datasets into smaller, manageable "pages" directly at the database level.
  - **How we use it:** Instead of the frontend requesting all events and filtering them in React, the backend uses SQLAlchemy's `limit`, `offset`, and `ilike` operators. The `GET /api/events` endpoint only retrieves the exact 25 rows requested and filters search terms (like an IP or title) directly inside PostgreSQL.
  - **Why it matters:** As the background pipeline ingests thousands of events, sending all of them to the frontend would crash the user's browser and consume massive bandwidth. Server-side pagination guarantees that the UI remains blazing fast and memory-efficient regardless of whether the database holds 100 or 1,000,000 events.

---

## 6. Frontend (The User Interface)

The Frontend is the visual dashboard that the analyst interacts with in their web browser.

- **React (with TypeScript):**
  - **What it is:** A JavaScript library for building user interfaces, paired with TypeScript for strict variable typing.
  - **How we use it:** React builds our UI using reusable "Components" (like the `CreateEventModal` or `Navbar`). TypeScript ensures that our components only accept the correct data shapes (e.g., ensuring an event always has a `severity` property), catching errors before the code even runs.
  - **Why it matters:** It allows us to build a dynamic, fast Single Page Application (SPA). When you delete an event, React instantly removes it from the screen without having to refresh the web page.

- **Vite:**
  - **What it is:** A blazing-fast build tool for modern web projects.
  - **How we use it:** Vite powers our local development server (`npm run dev`) and bundles our code for production (`npm run build`).
  - **Why it matters:** It replaces older, slower tools like Webpack, making the application compile almost instantly and keeping the developer experience smooth.

- **React Context API:**
  - **What it is:** A built-in React feature for managing "global" state across the entire application.
  - **How we use it:** We use `AuthContext` to store the currently logged-in user's token and profile. Any component in the app (like the Navbar or the Events Page) can instantly access the user's role to determine what to display, without having to pass data manually through every single layer of the app.
  - **Why it matters:** It provides a lightweight, highly efficient way to manage our authentication state without needing heavy external libraries like Redux.

- **Exponential Backoff (Network Resiliency):**
  - **What it is:** A mathematical algorithm for retrying failed network requests.
  - **How we use it:** In our `api.ts` file, our custom `fetchWithRetry` function intercepts API calls. If the backend is temporarily offline or overwhelmed (returning a 500-level error), the frontend doesn't just crash. It waits a fraction of a second, tries again, waits a bit longer, and tries again.
  - **Why it matters:** It makes the platform incredibly resilient to minor internet blips or server restarts, providing a seamless experience for the analyst.

- **XSS (Cross-Site Scripting) Mitigation:**
  - **What it is:** Preventing attackers from injecting malicious code into our web page.
  - **How we use it:** We strictly avoid using raw HTML injection commands like `dangerouslySetInnerHTML`. Instead, we rely entirely on React's native string interpolation (e.g., `{event.title}`).
  - **Why it matters:** If an attacker creates an event with a title like `<script>stealPasswords()</script>`, React will safely render it as plain text rather than executing the code, keeping our users 100% secure.

---

## 7. CI/CD & AI Workflows (The Automation)

This covers how we automate our testing, quality gates, and version control using modern automation tools and AI protocols.

- **GitHub Actions (Git Actions):**
  - **What it is:** A Continuous Integration and Continuous Deployment (CI/CD) platform integrated directly into GitHub.
  - **How we use it:** We rely on GitHub Actions to automatically trigger our mandatory system quality gates (like running `ruff check`, `mypy` for strict typing, and ESLint) whenever new code is pushed to the repository.
  - **Why it matters:** It acts as an automated, rigid gatekeeper. It guarantees that our strict backend and frontend quality standards are met on every single commit, preventing broken or vulnerable code from ever reaching production.

- **MCP Git (Model Context Protocol for Git):**
  - **What it is:** A specialized protocol that gives AI coding agents secure, standardized access to perform Git version control operations.
  - **How we use it:** We use MCP Git to power our Automated Branch Off-boarding Pipeline. The AI uses this protocol to automatically stage files, craft semantic commit messages, push active branches to the upstream origin, and instantly switch back to sync the stable `main` branch.
  - **Why it matters:** It seamlessly connects our AI-Driven Development (AIDD) workflow directly to version control. It removes the manual overhead of branching and committing, ensuring that our repository stays flawlessly organized and synchronized without the developer having to type a single Git command.

---

## 8. Infrastructure & Containerization (The Environment)

This section explains how we package and run our application reliably across different machines.

- **Docker:**
  - **What it is:** A platform that packages software into standardized, isolated units called "containers." A container includes everything the software needs to run (code, runtime, system tools, libraries) so it behaves identically on any computer.
  - **How we use it:** We wrap our FastAPI backend server and our PostgreSQL database in Docker containers (often orchestrated via Docker Compose). Instead of forcing every developer to manually install Python, PostgreSQL, and all the specific dependencies on their personal laptops, they simply run a Docker command to spin up the entire backend stack instantly.
  - **Why it matters:** It completely eliminates the "it works on my machine" problem. By containerizing the server and DB, we guarantee that the exact same environment running locally will be the one running in production. It makes onboarding new developers incredibly fast, isolates our dependencies to prevent system conflicts, and ensures our deployments are highly predictable and reliable.

---

## 9. Background Task Scheduling (The Heartbeat)

This covers how we run periodic maintenance, telemetry gathering, and asynchronous workflows without blocking the main web server.

- **Native Asyncio Event Loop:**
  - **What it is:** Python's built-in asynchronous I/O framework that powers FastAPI under the hood.
  - **How we use it:** Instead of deploying heavy external task queues like Celery or Redis, we bind our background tasks (like the heartbeat engine) directly to FastAPI's `lifespan` context manager using `asyncio.create_task()`.
  - **Why it matters:** It keeps our architecture exceptionally lightweight while perfectly guaranteeing that background jobs spin up safely when the server starts and shut down gracefully when the server stops, all without blocking incoming HTTP requests.

- **External API Ingestion (`httpx`):**
  - **What it is:** An asynchronous HTTP client for Python.
  - **How we use it:** Inside our background scheduler, we use `httpx.AsyncClient()` to routinely fetch the US Government's CISA KEV (Known Exploited Vulnerabilities) JSON feed.
  - **Why it matters:** Unlike the synchronous `requests` library, `httpx` allows our background task to wait for the CISA servers to respond without freezing the rest of the FastAPI application. This gives PenguWave real-time threat intelligence ingestion under the hood.
