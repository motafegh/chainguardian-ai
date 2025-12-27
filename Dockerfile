# ============================================================
# STAGE 1: BUILDER
# ============================================================
FROM python:3.11 AS builder

WORKDIR /build

ENV CUDA_VISIBLE_DEVICES="" \
    USE_CUDA=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.docker.txt ./requirements.txt

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# ============================================================
# STAGE 2: RUNTIME
# ============================================================
FROM python:3.11-slim AS runtime

ENV CUDA_VISIBLE_DEVICES="" \
    USE_CUDA=0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Slither for smart contract analysis
RUN pip install --no-cache-dir slither-analyzer==0.10.0

# Install solc-select and Solidity compiler
RUN pip install --no-cache-dir solc-select && \
    solc-select install 0.8.0 && \
    solc-select use 0.8.0

# Create non-root user and required directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/models /app/config && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy and install Python dependencies from builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy pyproject.toml
COPY --chown=appuser:appuser pyproject.toml /app/

# Copy configuration files (CRITICAL - ADD THIS!)
COPY --chown=appuser:appuser config/ /app/config/

# Copy application code
COPY --chown=appuser:appuser src/chainguardian /app/chainguardian

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$\{PORT:-8000\}/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Start command with dynamic port binding
CMD uvicorn chainguardian.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
