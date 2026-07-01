# ==============================================================================
# STMS Backend — Multi-stage Dockerfile
# ==============================================================================
# Build:  docker build -t stms-backend .
# Run:    docker run -p 8001:8001 --env-file .env stms-backend
# ==============================================================================

# ---- Stage 1: Builder (install Python deps) ----
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for building Python packages (numpy, opencv, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
COPY requirements.txt ./

# Use pip to install dependencies into a virtual env
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.11-slim AS runtime

# System libraries needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r stms && useradd -r -g stms -m stms

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY detectors/ ./detectors/
COPY optimization/ ./optimization/
COPY llm/ ./llm/
COPY ai_models/ ./ai_models/

# Create required directories
RUN mkdir -p logs snapshots uploads \
    && chown -R stms:stms /app

# Switch to non-root user
USER stms

# Expose the API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Run the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
