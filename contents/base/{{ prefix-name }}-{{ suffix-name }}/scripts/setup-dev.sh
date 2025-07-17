#!/bin/bash

# Complete development environment setup script

set -e

echo "🚀 Setting up Example Service Python development environment..."

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Python 3.11+ is required. Found: Python $PYTHON_VERSION"
    echo "   Please install Python 3.11 or later"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if Poetry is installed
if ! command -v poetry >/dev/null 2>&1; then
    echo "❌ Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v poetry >/dev/null 2>&1; then
        echo "❌ Poetry installation failed"
        exit 1
    fi
else
    echo "✅ Poetry found: $(poetry --version)"
fi

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found. Please install Docker first"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first"
    exit 1
fi

echo "✅ Docker is available and running"

# Check Docker Compose
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi

echo "✅ Docker Compose is available"

# Install Protocol Buffer Compiler
echo ""
echo "🔧 Setting up Protocol Buffer Compiler..."

if ! command -v protoc >/dev/null 2>&1; then
    echo "📥 Installing protoc..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew >/dev/null 2>&1; then
            brew install protobuf
        else
            echo "⚠️  Homebrew not found. Running manual protoc installation..."
            ./scripts/install-protoc.sh
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update
            sudo apt-get install -y protobuf-compiler
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y protobuf-compiler
        else
            echo "⚠️  Package manager not detected. Running manual protoc installation..."
            ./scripts/install-protoc.sh
        fi
    else
        echo "⚠️  OS not detected. Running manual protoc installation..."
        ./scripts/install-protoc.sh
    fi
else
    echo "✅ protoc already installed: $(protoc --version)"
fi

# Set up Python virtual environments for each module
echo ""
echo "📦 Setting up Python dependencies..."

MODULES=(
    "{{ prefix-name }}-{{ suffix-name }}-proto"
    "{{ prefix-name }}-{{ suffix-name }}-api" 
    "{{ prefix-name }}-{{ suffix-name }}-core"
    "{{ prefix-name }}-{{ suffix-name }}-persistence"
    "{{ prefix-name }}-{{ suffix-name }}-server"
    "{{ prefix-name }}-{{ suffix-name }}-client"
    "{{ prefix-name }}-{{ suffix-name }}-integration-tests"
)

for module in "${MODULES[@]}"; do
    if [[ -d "$module" ]]; then
        echo "   Setting up $module..."
        cd "$module"
        
        # Install dependencies
        poetry install --no-interaction
        
        # Verify installation
        if poetry run python -c "import sys; print(f'Python {sys.version}')" >/dev/null 2>&1; then
            echo "   ✅ $module dependencies installed"
        else
            echo "   ❌ Failed to set up $module"
            exit 1
        fi
        
        cd ..
    else
        echo "   ⚠️  Module directory not found: $module"
    fi
done

# Generate gRPC code
echo ""
echo "🔄 Generating gRPC code..."
if [[ -f "scripts/generate-grpc.sh" ]]; then
    ./scripts/generate-grpc.sh
else
    cd {{ prefix-name }}-{{ suffix-name }}-proto
    poetry run python build_proto.py
    cd ..
fi

# Set up pre-commit hooks
echo ""
echo "🪝 Setting up pre-commit hooks..."
cd {{ prefix-name }}-{{ suffix-name }}-integration-tests
if poetry run pre-commit --version >/dev/null 2>&1; then
    poetry run pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  Pre-commit not available, skipping hooks setup"
fi
cd ..

# Create local environment file
echo ""
echo "📝 Creating local environment configuration..."

if [[ ! -f ".env.local" ]]; then
    cat > .env.local << EOF
# Local development environment variables
# Copy this file to .env and modify as needed

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/{{ prefix_name }}_{{ suffix_name }}
DATABASE_ECHO=false

# gRPC Server
GRPC_PORT=9010
GRPC_REFLECTION_ENABLED=true
GRPC_MAX_WORKERS=10

# Management Server  
MANAGEMENT_PORT=9011
MANAGEMENT_ENABLED=true

# Logging
LOGGING_LEVEL=INFO
LOGGING_FORMAT=console

# Metrics
METRICS_ENABLED=true
METRICS_PROMETHEUS_ENABLED=true

# Development
DEBUG=true
ENVIRONMENT=development
EOF

    echo "✅ Created .env.local template"
    echo "   Copy to .env and modify for your local setup"
else
    echo "✅ .env.local already exists"
fi

# Test the setup
echo ""
echo "🧪 Testing the development setup..."

# Test imports
echo "   Testing Python imports..."
cd {{ prefix-name }}-{{ suffix-name }}-integration-tests
if poetry run python -c "
import sys
sys.path.insert(0, '../{{ prefix-name }}-{{ suffix-name }}-proto/src')
try:
    import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2 as pb2
    print('✅ gRPC imports work')
except ImportError as e:
    print(f'❌ gRPC import failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo "   ✅ Import test passed"
else
    echo "   ❌ Import test failed"
fi
cd ..

# Test Docker build
echo "   Testing Docker build..."
if docker build -t {{ prefix-name }}-{{ suffix-name }}:dev-test . >/dev/null 2>&1; then
    echo "   ✅ Docker build test passed"
    docker rmi {{ prefix-name }}-{{ suffix-name }}:dev-test >/dev/null 2>&1 || true
else
    echo "   ❌ Docker build test failed"
fi

echo ""
echo "🎉 Development environment setup completed!"
echo ""
echo "📋 Summary:"
echo "   ✅ Python 3.11+ installed"
echo "   ✅ Poetry installed and configured"
echo "   ✅ Docker and Docker Compose available"
echo "   ✅ Protocol Buffer Compiler installed"
echo "   ✅ All module dependencies installed"
echo "   ✅ gRPC code generated"
echo "   ✅ Development configuration created"
echo ""
echo "🚀 Next steps:"
echo "   1. Copy .env.local to .env and customize settings"
echo "   2. Start development environment: ./scripts/start-dev.sh"
echo "   3. Run tests: ./scripts/run-tests.sh"
echo "   4. Check service health: curl http://localhost:9011/health"
echo ""
echo "💡 Useful commands:"
echo "   ./scripts/start-dev.sh      - Start all services"
echo "   ./scripts/run-tests.sh      - Run all tests"
echo "   ./scripts/generate-grpc.sh  - Regenerate gRPC code"
echo "   docker-compose logs -f      - View service logs"