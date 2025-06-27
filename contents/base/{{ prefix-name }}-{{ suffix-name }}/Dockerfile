# Multi-stage Docker build for Example Service
FROM python:3.11-slim as builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including protoc
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    unzip \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set work directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-proto/src ./{{ prefix-name }}-{{ suffix-name }}-proto/src
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-api/src ./{{ prefix-name }}-{{ suffix-name }}-api/src
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-core/src ./{{ prefix-name }}-{{ suffix-name }}-core/src
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-persistence/src ./{{ prefix-name }}-{{ suffix-name }}-persistence/src
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-server/src ./{{ prefix-name }}-{{ suffix-name }}-server/src
COPY --chown=appuser:appuser {{ prefix-name }}-{{ suffix-name }}-client/src ./{{ prefix-name }}-{{ suffix-name }}-client/src

# Copy scripts
COPY --chown=appuser:appuser scripts/ ./scripts/

# Copy project configuration
COPY --chown=appuser:appuser pyproject.toml ./

# Build will automatically generate gRPC code
# No manual generation needed

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 9010 9011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9011/health/live || exit 1

# Default command
CMD ["python", "-m", "{{ org-name }}.{{ solution-name }}.example_service.server.main"]