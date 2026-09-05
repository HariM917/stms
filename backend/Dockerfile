# ==============================================================================
# STMS Backend — Production Hardened Multi-stage Dockerfile
# ==============================================================================
# Build:  docker build -t stms-backend .
# Run:    docker run -p 8001:8001 --env-file .env stms-backend
# ==============================================================================

# ---- Stage 1: Builder (install Python deps) ----
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# System dependencies for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.11-slim-bookworm AS runtime

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root service user
RUN groupadd -r stms && useradd -r -g stms -m stms

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy application and ML packages
COPY app/ ./app/
COPY detectors/ ./detectors/
COPY optimization/ ./optimization/
COPY llm/ ./llm/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Create runtime volume mount points and operational directories with non-root ownership
RUN mkdir -p /app/ai_models /app/models logs snapshots uploads \
    && chown -R stms:stms /app

USER stms

EXPOSE 8001

# Production readiness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8001/api/health/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
