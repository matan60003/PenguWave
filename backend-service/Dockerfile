# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (e.g., for building C extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Create a virtual environment to isolate dependencies cleanly
RUN python -m venv /opt/venv

# Ensure virtual environment binaries are used for pip installs
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into the virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production runner image
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy the pre-compiled virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Configure environment variables
# 1. Update PATH to check our virtual environment binaries first
# 2. Prevent writing .pyc files
# 3. Stream logs without buffering
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a secure, non-privileged system user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin appuser

# Copy the application source code
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 8000

# Default entrypoint using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
