"""Generate gRPC code from Protocol Buffer definitions using Poetry."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a command and return success status."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_protoc() -> bool:
    """Check if protoc is available."""
    try:
        subprocess.run(["protoc", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_protoc() -> bool:
    """Install protoc using the install script."""
    script_path = Path(__file__).parent / "install-protoc.sh"
    if script_path.exists():
        return run_command(["bash", str(script_path)])
    else:
        print("install-protoc.sh not found. Please install protoc manually.")
        return False


def fix_imports(file_path: Path) -> None:
    """Fix import statements in generated gRPC files."""
    if not file_path.exists():
        return
    
    content = file_path.read_text()
    
    # Fix absolute imports to relative imports
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.startswith('import ') and '_pb2' in line:
            # Convert absolute imports to relative imports
            parts = line.split('.')
            if len(parts) > 1 and '{{ org-name }}' in parts[0]:
                # Extract just the module name
                module_name = parts[-1].replace(' as ', '_as_').split('_as_')[0]
                if '_as_' in parts[-1]:
                    alias = parts[-1].split('_as_')[1]
                    line = f"from . import {module_name} as {alias}"
                else:
                    line = f"from . import {module_name}"
        
        fixed_lines.append(line)
    
    file_path.write_text('\n'.join(fixed_lines))


def generate_grpc_code() -> bool:
    """Generate gRPC code from proto files."""
    root_dir = Path(__file__).parent.parent
    proto_dir = root_dir / "{{ prefix-name }}-{{ suffix-name }}-proto"
    proto_src_dir = proto_dir / "src"
    proto_file = proto_src_dir / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc" / "{{ prefix_name }}_{{ suffix_name }}.proto"
    
    if not proto_file.exists():
        print(f"Proto file not found: {proto_file}")
        return False
    
    # Change to proto directory
    os.chdir(proto_dir)
    
    # Generate Python code
    cmd = [
        "python", "-m", "grpc_tools.protoc",
        f"--proto_path={proto_src_dir}",
        f"--python_out={proto_src_dir}",
        f"--grpc_python_out={proto_src_dir}",
        str(proto_file.relative_to(proto_src_dir))
    ]
    
    if not run_command(cmd):
        return False
    
    # Fix imports in generated files
    generated_dir = proto_src_dir / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc"
    
    for file_path in generated_dir.glob("*_pb2_grpc.py"):
        fix_imports(file_path)
    
    print("✅ gRPC code generation completed successfully")
    return True


def main() -> None:
    """Main entry point."""
    print("🔄 Generating gRPC code from Protocol Buffers...")
    
    # Check if protoc is available
    if not check_protoc():
        print("❌ protoc not found. Attempting to install...")
        if not install_protoc():
            print("❌ Failed to install protoc. Please install manually.")
            sys.exit(1)
    
    # Generate gRPC code
    if not generate_grpc_code():
        print("❌ Failed to generate gRPC code")
        sys.exit(1)
    
    print("✅ gRPC code generation completed successfully")


if __name__ == "__main__":
    main()