# {{ PrefixName }} {{ SuffixName }} Python

A modular, enterprise-grade Python gRPC {{ suffix-name }} with automatic build pipeline and modern tooling.

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **uv** (modern Python package manager)
- **Docker & Docker Compose** (for database)
- **protoc** (Protocol Buffer compiler) - or use `nix-shell`

### Quick Setup

```bash
# 1. Install dependencies
uv sync --dev

# 2. Start database
docker-compose up postgres -d

# 3. Run migrations
uv run {{ prefix-name }}-{{ suffix-name }}-migrate upgrade

# 4. Start the server
uv run {{ prefix-name }}-{{ suffix-name }}-server
```

**That's it!** The server runs on:
- **gRPC**: `localhost:9010`
- **HTTP** (health/metrics): `localhost:8080` (or `localhost:9011` when using Docker)

### Alternative: Ephemeral Database

For development without Docker Compose, use the built-in ephemeral database:

```bash
# 1. Install dependencies
uv sync --dev

# 2. Start server with ephemeral database (auto-starts TestContainers PostgreSQL)
./scripts/run-server-ephemeral.sh
```

**Requirements**: Docker must be running (Docker Desktop, Rancher Desktop, etc.)

**Connection Information**: When the ephemeral database starts, detailed connection information is logged to help you connect with database tools:

```
================================================================================
🐘 EPHEMERAL POSTGRESQL DATABASE CONNECTION INFO
================================================================================

📋 Connection Details:
   Host:     localhost
   Port:     54321  (randomized port)
   Database: {{ prefix_name }}_{{ suffix_name }}
   Username: postgres
   Password: postgres

💻 Connect via psql:
   psql -h localhost -p 54321 -U postgres -d {{ prefix_name }}_{{ suffix_name }}

🔧 DataGrip/Database Tool Settings:
   Type:     PostgreSQL
   Host:     localhost
   Port:     54321
   Database: {{ prefix_name }}_{{ suffix_name }}
   User:     postgres
   Password: postgres
================================================================================
```

### Quick Test

```bash
# Health check
curl http://localhost:8080/health

# gRPC test (requires grpcurl)
grpcurl -plaintext -d '{"{{ prefix_name }}": {"name": "test", "description": "Test {{ prefix-name }}"}}' \
  localhost:9010 {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ PrefixName }}{{ SuffixName }}/Create{{ PrefixName }}
```

## 🏗️ Build System

This project features an **automatic build pipeline** that handles code generation:

```bash
# Automatic gRPC generation + build
uv build

# Manual gRPC generation (development)
uv run generate-grpc
```

The build system automatically:
- ✅ Generates gRPC code from protobuf files
- ✅ Validates project structure
- ✅ Fixes Python imports
- ✅ Provides extensible pipeline for future build steps

## 📋 Essential Commands

### Development
```bash
uv sync --dev                          # Install dependencies with dev tools
uv run {{ prefix-name }}-{{ suffix-name }}-server          # Start server
uv build                               # Build with automatic gRPC generation
```

### Database
```bash
uv run {{ prefix-name }}-{{ suffix-name }}-migrate upgrade  # Run migrations
uv run {{ prefix-name }}-{{ suffix-name }}-migrate current  # Check migration status
```

### Testing
```bash
uv run pytest                          # All tests
uv run pytest -m unit                  # Unit tests only
uv run pytest -m integration           # Integration tests only
```

### Code Quality
```bash
uv run black . && uv run isort . && uv run flake8  # Format and lint
uv run mypy                            # Type checking
```

## 🏛️ Architecture

Modular design with clear separation of concerns:

```
{{ prefix-name }}-{{ suffix-name }}-python/
├── {{ prefix-name }}-{{ suffix-name }}-proto/        # Protocol Buffer definitions
├── {{ prefix-name }}-{{ suffix-name }}-api/          # {{ SuffixName }} interfaces and DTOs
├── {{ prefix-name }}-{{ suffix-name }}-core/         # Business logic implementation
├── {{ prefix-name }}-{{ suffix-name }}-persistence/  # Database entities and repositories
├── {{ prefix-name }}-{{ suffix-name }}-server/       # gRPC server and HTTP endpoints
├── {{ prefix-name }}-{{ suffix-name }}-client/       # Client library
└── {{ prefix-name }}-{{ suffix-name }}-integration-tests/ # End-to-end testing
```

## ✨ Enterprise Features

### Core Capabilities
- **gRPC-First**: Protocol Buffers with automatic code generation
- **Async/Await**: Full async implementation using asyncio
- **Database**: SQLAlchemy 2.0 with Alembic migrations
- **Testing**: pytest with TestContainers for integration tests

### Observability
- **Structured Logging**: JSON logging with correlation IDs
- **Metrics**: Prometheus with custom business metrics
- **Health Checks**: Kubernetes-ready endpoints (`/health`, `/health/live`, `/health/ready`)
- **Tracing**: OpenTelemetry integration

### Enterprise Middleware
- **Authentication**: JWT with role-based authorization
- **Rate Limiting**: Token bucket algorithm
- **Circuit Breaker**: Resilience patterns
- **Correlation IDs**: Request tracing across services

## 🔧 Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/{{ prefix_name }}_{{ suffix_name }}

# Server Ports
GRPC_PORT=9010                    # gRPC {{ suffix-name }} port
HTTP_PORT=8080                    # Health/metrics port

# Logging
LOG_LEVEL=INFO                    # Application log level
ENVIRONMENT=development           # Deployment environment
```

## 🐳 Docker

### Development
```bash
# Start all services (database + monitoring)
docker-compose up -d

# Build and run {{ suffix-name }}
docker build -t {{ prefix-name }}-{{ suffix-name }} .
docker run -p 9010:9010 -p 9011:8080 {{ prefix-name }}-{{ suffix-name }}
```

### Production
The Dockerfile uses **multi-stage builds** with uv for fast, secure containers:
- Non-root execution
- Minimal dependencies
- Automatic gRPC generation during build

## 📊 Monitoring

### Included Monitoring Stack
```bash
docker-compose up -d  # Includes Prometheus + Grafana
```

- **Grafana**: `http://localhost:3000` (dashboards included)
- **Prometheus**: `http://localhost:9090` (metrics collection)
- **Application Metrics**: `http://localhost:8080/metrics`

### Key Metrics
- gRPC request rates, latencies, error rates
- Database connection pool status
- Custom business metrics
- Health check status

## 🧪 Testing

### Test Categories
- **Unit Tests**: Fast, isolated component testing
- **Integration Tests**: Database and service integration with TestContainers
- **End-to-End Tests**: Complete workflow testing

### Running Tests
```bash
# All tests
uv run pytest

# Specific categories
uv run pytest -m unit
uv run pytest -m integration

# With coverage
uv run pytest --cov={{ org-name }} --cov-report=html
```

## 🔒 Security

- **Container Security**: Non-root execution, minimal base image
- **Database Security**: Parameterized queries, connection pooling
- **Network Security**: Port isolation, secure configuration
- **Authentication**: JWT-based auth with role-based access control

## 📈 Performance

- **Async Architecture**: Full asyncio implementation
- **Connection Pooling**: Configurable database connection management
- **gRPC Optimizations**: Compression, worker thread tuning
- **Caching**: Redis integration for performance-critical paths

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Run `uv sync --dev` to set up environment
3. Make changes with tests
4. Run `uv run pytest` and code quality checks
5. Submit a pull request

### Code Quality Standards
- **Type Hints**: Full type annotation coverage
- **Formatting**: Black and isort for consistent code style
- **Linting**: Comprehensive checks with flake8 and mypy
- **Testing**: Maintain high test coverage

## 📚 More Information

- **Detailed Commands**: See [CLAUDE.md](CLAUDE.md) for comprehensive command reference
- **API Documentation**: Protocol buffer definitions in `{{ prefix-name }}-{{ suffix-name }}-proto/`
- **Health Endpoints**: Kubernetes-compatible health checks at `/health/*`