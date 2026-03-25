# Xcleaners — Multi-stage Dockerfile

# Stage 1: Builder — installs all deps (including build tools)
FROM python:3.12-slim AS builder
WORKDIR /build

# Build-time system deps needed to compile native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libjpeg-dev zlib1g-dev libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — lean image with no build tools
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Only runtime system deps (shared libs for Pillow, asyncpg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo libpng16-16 libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only production dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy application code only — no tests, scripts, or docs
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY xcleaners_main.py .
COPY database/ ./database/

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=5 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\",\"8003\")}/health')"

CMD sh -c "uvicorn xcleaners_main:app --host 0.0.0.0 --port ${PORT:-8003}"
