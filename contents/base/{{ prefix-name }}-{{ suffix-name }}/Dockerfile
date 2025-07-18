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

# Copy all package configurations
COPY pyproject.toml uv.lock* ./
COPY {{ prefix-name }}-{{ suffix-name }}-proto/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-proto/
COPY {{ prefix-name }}-{{ suffix-name }}-core/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-core/
COPY {{ prefix-name }}-{{ suffix-name }}-persistence/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-persistence/
COPY {{ prefix-name }}-{{ suffix-name }}-api/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-api/
COPY {{ prefix-name }}-{{ suffix-name }}-client/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-client/
COPY {{ prefix-name }}-{{ suffix-name }}-server/pyproject.toml ./{{ prefix-name }}-{{ suffix-name }}-server/

# Copy all source code
COPY {{ prefix-name }}-{{ suffix-name }}-proto/src ./{{ prefix-name }}-{{ suffix-name }}-proto/src/
COPY {{ prefix-name }}-{{ suffix-name }}-core/src ./{{ prefix-name }}-{{ suffix-name }}-core/src/
COPY {{ prefix-name }}-{{ suffix-name }}-persistence/src ./{{ prefix-name }}-{{ suffix-name }}-persistence/src/
COPY {{ prefix-name }}-{{ suffix-name }}-api/src ./{{ prefix-name }}-{{ suffix-name }}-api/src/
COPY {{ prefix-name }}-{{ suffix-name }}-client/src ./{{ prefix-name }}-{{ suffix-name }}-client/src/
COPY {{ prefix-name }}-{{ suffix-name }}-server/src ./{{ prefix-name }}-{{ suffix-name }}-server/src/

# Copy scripts and proto files
COPY scripts ./scripts
COPY {{ prefix-name }}-{{ suffix-name }}-proto/src/{{ org_name }}/{{ solution_name }}/{{ prefix_name }}/{{ suffix_name }}/grpc/*.proto ./{{ prefix-name }}-{{ suffix-name }}-proto/src/{{ org_name }}/{{ solution_name }}/{{ prefix_name }}/{{ suffix_name }}/grpc/

# Install dependencies (this will build proto and install all packages)
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

# Copy virtual environment and full application from builder stage
COPY --from=builder --chown=appuser:appuser /app /app

# Build will automatically generate gRPC code
# No manual generation needed

# Switch to non-root user
USER appuser

# Set working directory to server package to avoid namespace conflicts
WORKDIR /app/{{ prefix-name }}-{{ suffix-name }}-server/src

# Expose ports
EXPOSE 9010 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health/live || exit 1

# Default command  
CMD ["python", "-m", "{{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.server.main"]