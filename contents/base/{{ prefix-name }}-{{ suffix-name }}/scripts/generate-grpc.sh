#!/bin/bash

# gRPC Code Generation Script
# Generates Python gRPC stubs from Protocol Buffer definitions

set -e

echo "🔧 Generating Python gRPC code from Protocol Buffers..."

# Check if protoc is available
if ! command -v protoc >/dev/null 2>&1; then
    echo "❌ protoc not found. Please install Protocol Buffer Compiler first:"
    echo "   ./scripts/install-protoc.sh"
    exit 1
fi

# Check if we're in the project root
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install grpcio-tools if not available
echo "📦 Ensuring grpcio-tools is available..."
python3 -c "import grpc_tools" 2>/dev/null || {
    echo "📥 Installing grpcio-tools..."
    pip install grpcio-tools protobuf
}

# Set up directories
PROTO_SRC_DIR="{{ prefix-name }}-{{ suffix-name }}-proto/src"
PROTO_OUT_DIR="{{ prefix-name }}-{{ suffix-name }}-proto/src"

if [[ ! -d "$PROTO_SRC_DIR" ]]; then
    echo "❌ Proto source directory not found: $PROTO_SRC_DIR"
    exit 1
fi

echo "📂 Proto source: $PROTO_SRC_DIR"
echo "📂 Output directory: $PROTO_OUT_DIR"

# Find all .proto files
PROTO_FILES=$(find "$PROTO_SRC_DIR" -name "*.proto" | sort)

if [[ -z "$PROTO_FILES" ]]; then
    echo "❌ No .proto files found in $PROTO_SRC_DIR"
    exit 1
fi

echo "📋 Found proto files:"
for file in $PROTO_FILES; do
    echo "   - $file"
done

# Generate Python code for each proto file
echo ""
echo "🔄 Generating Python gRPC code..."

for proto_file in $PROTO_FILES; do
    echo "   Processing: $proto_file"
    
    # Calculate relative path from proto source directory
    rel_path=$(realpath --relative-to="$PROTO_SRC_DIR" "$proto_file")
    
    # Generate Python code
    python3 -m grpc_tools.protoc \
        --proto_path="$PROTO_SRC_DIR" \
        --python_out="$PROTO_OUT_DIR" \
        --grpc_python_out="$PROTO_OUT_DIR" \
        "$rel_path"
    
    if [[ $? -eq 0 ]]; then
        echo "   ✅ Generated code for $rel_path"
    else
        echo "   ❌ Failed to generate code for $rel_path"
        exit 1
    fi
done

# Fix import paths in generated files
echo ""
echo "🔧 Fixing import paths in generated files..."

# Find generated _pb2_grpc.py files and fix their imports
find "$PROTO_OUT_DIR" -name "*_pb2_grpc.py" | while read -r grpc_file; do
    # Get the corresponding _pb2.py file name
    pb2_file=$(basename "$grpc_file" "_grpc.py").py
    pb2_module=$(basename "$grpc_file" "_pb2_grpc.py")_pb2
    
    # Check if the import needs to be fixed (relative import)
    if grep -q "import ${pb2_module}" "$grpc_file"; then
        echo "   Fixing imports in $(basename "$grpc_file")"
        
        # Create backup
        cp "$grpc_file" "$grpc_file.bak"
        
        # Fix the import to be relative
        sed -i.tmp "s/import ${pb2_module}/from . import ${pb2_module}/g" "$grpc_file"
        rm -f "$grpc_file.tmp"
        
        echo "   ✅ Fixed imports in $(basename "$grpc_file")"
    fi
done

# Generate __init__.py files if they don't exist
echo ""
echo "📝 Ensuring __init__.py files exist..."

find "$PROTO_OUT_DIR" -type d | while read -r dir; do
    init_file="$dir/__init__.py"
    if [[ ! -f "$init_file" ]]; then
        touch "$init_file"
        echo "   Created: $init_file"
    fi
done

# Show generated files
echo ""
echo "📋 Generated files:"
find "$PROTO_OUT_DIR" -name "*_pb2.py" -o -name "*_pb2_grpc.py" | sort | while read -r file; do
    echo "   ✅ $file"
done

# Verify imports work
echo ""
echo "🔍 Verifying generated code..."

# Test import of generated modules
cd {{ prefix-name }}-{{ suffix-name }}-proto

python3 -c "
import sys
import os
sys.path.insert(0, 'src')

try:
    # Try to import generated modules
    import {{ org-name }}.{{ solution-name }}.example_service.grpc.v1.example_service_v1_pb2 as pb2
    import {{ org-name }}.{{ solution-name }}.example_service.grpc.v1.example_service_v1_pb2_grpc as pb2_grpc
    print('✅ Generated modules can be imported successfully')
    
    # Test basic functionality
    request = pb2.GetExamplesRequest()
    request.start_page = 0
    request.page_size = 10
    print('✅ Protocol buffer messages work correctly')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error testing generated code: {e}')
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    echo "✅ Code generation verification passed!"
else
    echo "❌ Code generation verification failed!"
    exit 1
fi

cd ..

echo ""
echo "🎉 gRPC code generation completed successfully!"
echo ""
echo "📝 Generated files are ready to use:"
echo "   - Protocol buffer messages: *_pb2.py"
echo "   - gRPC service stubs: *_pb2_grpc.py"
echo ""
echo "💡 Next steps:"
echo "   1. Update imports in your service implementation"
echo "   2. Run tests to verify everything works: ./scripts/run-tests.sh"
echo "   3. Start the development environment: ./scripts/start-dev.sh"