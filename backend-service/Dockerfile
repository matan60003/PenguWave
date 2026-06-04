# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies if needed (e.g., for building C extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a user-local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runner image
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy the installed site-packages from the builder stage
COPY --from=builder /root/.local /root/.local

# Configure environment variables
# 1. Update PATH to include the user-installed binaries
# 2. Prevent writing .pyc files
# 3. Stream logs without buffering
ENV PATH=/root/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a secure, non-privileged system user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin appuser

# Copy the application source code
COPY . .

# Change ownership to the non-privileged user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 8000

# Default entrypoint using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
