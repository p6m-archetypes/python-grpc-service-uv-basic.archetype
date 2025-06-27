#!/usr/bin/env python3
"""Build script for generating Python gRPC stubs from proto files."""

import os
import subprocess
import sys
from pathlib import Path


def check_protoc_available():
    """Check if protoc is available in the system."""
    try:
        result = subprocess.run(["protoc", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"Found protoc: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ protoc not found. Please install Protocol Buffer Compiler:")
        print("   Linux/macOS: ./scripts/install-protoc.sh")
        print("   Or install via package manager:")
        print("     - Ubuntu/Debian: apt-get install protobuf-compiler")
        print("     - macOS: brew install protobuf")
        print("     - Windows: choco install protoc")
        return False


def check_grpc_tools_available():
    """Check if grpcio-tools is available."""
    try:
        import grpc_tools.protoc
        print("✅ grpcio-tools is available")
        return True
    except ImportError:
        print("❌ grpcio-tools not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "grpcio-tools", "protobuf"], 
                         check=True)
            print("✅ grpcio-tools installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install grpcio-tools")
            return False


def fix_import_paths(proto_dir):
    """Fix import paths in generated _pb2_grpc.py files."""
    grpc_files = list(proto_dir.rglob("*_pb2_grpc.py"))
    
    for grpc_file in grpc_files:
        print(f"Fixing imports in {grpc_file.name}")
        
        # Read the file
        content = grpc_file.read_text()
        
        # Find and fix imports
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix imports like "import {{ prefix_name }}_{{ suffix_name }}_pb2 as example__service__pb2"
            if line.strip().startswith('import ') and '_pb2 as ' in line and not line.strip().startswith('from '):
                # Extract module name
                import_parts = line.strip().split()
                if len(import_parts) >= 4 and import_parts[0] == 'import' and import_parts[2] == 'as':
                    module_name = import_parts[1]
                    alias = import_parts[3]
                    fixed_line = f"from . import {module_name} as {alias}"
                    fixed_lines.append(fixed_line)
                    print(f"   Fixed: {line.strip()} -> {fixed_line}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Write back if changes were made
        fixed_content = '\n'.join(fixed_lines)
        if fixed_content != content:
            grpc_file.write_text(fixed_content)
            print(f"   ✅ Updated {grpc_file.name}")
        else:
            print(f"   ⏭️  No changes needed for {grpc_file.name}")


def ensure_init_files(proto_dir):
    """Ensure __init__.py files exist in all directories."""
    directories = [d for d in proto_dir.rglob("*") if d.is_dir()]
    
    for directory in directories:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file.relative_to(proto_dir)}")


def verify_generated_code(proto_dir):
    """Verify that generated code can be imported."""
    print("🔍 Verifying generated code...")
    
    # Add the proto src directory to Python path temporarily
    import sys
    original_path = sys.path[:]
    sys.path.insert(0, str(proto_dir))
    
    try:
        # Try to import the generated modules
        import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2 as pb2
        import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2_grpc as pb2_grpc
        
        # Test basic functionality
        request = pb2.Get{{ PrefixName }}sRequest()
        request.start_page = 0
        request.page_size = 10
        
        print("✅ Generated modules imported and work correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing generated code: {e}")
        return False
    finally:
        # Restore original Python path
        sys.path[:] = original_path


def generate_grpc_code():
    """Generate Python gRPC code from proto files."""
    print("🔧 Generating Python gRPC stubs from Protocol Buffers...")
    
    # Check prerequisites
    if not check_protoc_available():
        sys.exit(1)
    
    if not check_grpc_tools_available():
        sys.exit(1)
    
    proto_dir = Path(__file__).parent / "src"
    output_dir = proto_dir
    
    if not proto_dir.exists():
        print(f"❌ Proto directory not found: {proto_dir}")
        sys.exit(1)
    
    proto_files = list(proto_dir.rglob("*.proto"))
    
    if not proto_files:
        print(f"❌ No proto files found in {proto_dir}")
        sys.exit(1)
    
    print(f"📋 Found {len(proto_files)} proto file(s):")
    for proto_file in proto_files:
        print(f"   - {proto_file.relative_to(proto_dir)}")
    
    # Generate code for each proto file
    print("\n🔄 Generating Python code...")
    for proto_file in proto_files:
        print(f"   Processing: {proto_file.relative_to(proto_dir)}")
        
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file.relative_to(proto_dir))
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error generating code for {proto_file}:")
            print(result.stderr)
            sys.exit(1)
        else:
            print(f"   ✅ Generated code for {proto_file.relative_to(proto_dir)}")
    
    # Post-processing
    print("\n🔧 Post-processing generated files...")
    fix_import_paths(proto_dir)
    ensure_init_files(proto_dir)
    
    # Verify the generated code
    if verify_generated_code(proto_dir):
        print("\n🎉 gRPC code generation completed successfully!")
        
        # Show generated files
        generated_files = list(proto_dir.rglob("*_pb2.py")) + list(proto_dir.rglob("*_pb2_grpc.py"))
        print(f"\n📋 Generated {len(generated_files)} files:")
        for file in sorted(generated_files):
            print(f"   ✅ {file.relative_to(proto_dir)}")
    else:
        print("\n❌ gRPC code generation verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    generate_grpc_code()