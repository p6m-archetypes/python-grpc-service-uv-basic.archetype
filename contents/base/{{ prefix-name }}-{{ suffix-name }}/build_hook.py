"""Hatchling build hook for automatic gRPC code generation."""

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class GrpcBuildHook(BuildHookInterface):
    """Build hook that automatically generates gRPC code before building."""
    
    PLUGIN_NAME = "grpc-build-hook"
    
    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize the build hook and run gRPC generation."""
        # Check if gRPC generation is needed to avoid double execution
        if self._should_skip_generation():
            print("⚡ [GRPC BUILD HOOK] Skipping - gRPC code already generated this session")
            return
            
        print("🔄 [GRPC BUILD HOOK] Starting gRPC code generation pipeline...")
        
        try:
            self._run_build_pipeline()
            self._mark_generation_complete()
            print("✅ [GRPC BUILD HOOK] Build pipeline completed successfully")
        except Exception as e:
            print(f"❌ [GRPC BUILD HOOK] Build pipeline failed: {e}")
            # Don't fail the build for gRPC generation issues
            print("⚠️  [GRPC BUILD HOOK] Continuing build - ensure gRPC files exist")
    
    def _should_skip_generation(self) -> bool:
        """Check if gRPC generation should be skipped (already done this session)."""
        root_path = Path(self.root)
        proto_file = root_path / "{{ prefix-name }}-{{ suffix-name }}-proto" / "src" / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc" / "{{ prefix_name }}_{{ suffix_name }}.proto"
        generated_file = root_path / "{{ prefix-name }}-{{ suffix-name }}-proto" / "src" / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc" / "{{ prefix_name }}_{{ suffix_name }}_pb2.py"
        marker_file = root_path / ".grpc_generation_marker"
        
        if not proto_file.exists() or not generated_file.exists():
            return False
        
        # Check if marker exists and is recent
        if marker_file.exists():
            try:
                marker_content = marker_file.read_text().strip()
                proto_hash = self._get_file_hash(proto_file)
                return marker_content == proto_hash
            except Exception:
                pass
        
        return False
    
    def _mark_generation_complete(self) -> None:
        """Mark that gRPC generation has been completed this session."""
        root_path = Path(self.root)
        proto_file = root_path / "{{ prefix-name }}-{{ suffix-name }}-proto" / "src" / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc" / "{{ prefix_name }}_{{ suffix_name }}.proto"
        marker_file = root_path / ".grpc_generation_marker"
        
        if proto_file.exists():
            proto_hash = self._get_file_hash(proto_file)
            marker_file.write_text(proto_hash)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get a hash of the file content for change detection."""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def _run_build_pipeline(self) -> None:
        """Execute the complete build pipeline."""
        # Environment validation
        self._validate_build_environment()
        
        # gRPC code generation (critical step)
        self._generate_grpc_code()
        
        # Future build steps can be added here:
        # self._generate_openapi_spec()
        # self._compile_assets()
        # self._generate_documentation()
    
    def _validate_build_environment(self) -> None:
        """Validate the build environment and dependencies."""
        print("🔍 [VALIDATION] Checking build environment...")
        
        # Check for required directories
        required_dirs = [
            "{{ prefix-name }}-{{ suffix-name }}-proto/src",
            "{{ prefix-name }}-{{ suffix-name }}-api/src", 
            "{{ prefix-name }}-{{ suffix-name }}-core/src",
            "{{ prefix-name }}-{{ suffix-name }}-persistence/src",
            "{{ prefix-name }}-{{ suffix-name }}-server/src",
            "{{ prefix-name }}-{{ suffix-name }}-client/src"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(self.root) / dir_path
            if not full_path.exists():
                print(f"⚠️  [VALIDATION] Directory not found: {dir_path}")
            else:
                print(f"✅ [VALIDATION] Found directory: {dir_path}")
    
    def _check_protoc(self) -> bool:
        """Check if protoc is available."""
        try:
            subprocess.run(["protoc", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _generate_grpc_code(self) -> None:
        """Generate gRPC code from Protocol Buffer definitions."""
        if not self._check_protoc():
            print("❌ [GRPC] protoc not found. Please install protoc.")
            raise RuntimeError("protoc not available")
        
        root_path = Path(self.root)
        proto_dir = root_path / "{{ prefix-name }}-{{ suffix-name }}-proto"
        proto_src_dir = proto_dir / "src"
        proto_file = proto_src_dir / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc" / "{{ prefix_name }}_{{ suffix_name }}.proto"
        
        if not proto_file.exists():
            print(f"❌ [GRPC] Proto file not found: {proto_file}")
            raise FileNotFoundError(f"Proto file not found: {proto_file}")
        
        print(f"🔄 [GRPC] Generating gRPC code from {proto_file.name}")
        
        # Generate Python code using grpc_tools.protoc
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_src_dir}",
            f"--python_out={proto_src_dir}",
            f"--grpc_python_out={proto_src_dir}",
            str(proto_file.relative_to(proto_src_dir))
        ]
        
        try:
            print(f"[GRPC] Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=root_path, check=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"[GRPC] {result.stdout}")
                
            # Fix imports in generated files
            self._fix_grpc_imports(proto_src_dir)
            
            print("✅ [GRPC] gRPC code generation completed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ [GRPC] gRPC generation failed: {e}")
            if e.stderr:
                print(f"[GRPC] stderr: {e.stderr}")
            raise
    
    def _fix_grpc_imports(self, proto_src_dir: Path) -> None:
        """Fix import statements in generated gRPC files."""
        generated_dir = proto_src_dir / "{{ org_name }}" / "{{ solution_name }}" / "{{ prefix_name }}" / "{{ suffix_name }}" / "grpc"
        
        for file_path in generated_dir.glob("*_pb2_grpc.py"):
            if not file_path.exists():
                continue
                
            try:
                content = file_path.read_text()
                lines = content.split('\n')
                fixed_lines = []
                
                for line in lines:
                    if line.startswith('import ') and '_pb2' in line:
                        # Convert absolute imports to relative imports
                        parts = line.split('.')
                        if len(parts) > 1 and '{{ org_name }}' in parts[0]:
                            # Extract just the module name
                            module_name = parts[-1].replace(' as ', '_as_').split('_as_')[0]
                            if '_as_' in parts[-1]:
                                alias = parts[-1].split('_as_')[1]
                                line = f"from . import {module_name} as {alias}"
                            else:
                                line = f"from . import {module_name}"
                    
                    fixed_lines.append(line)
                
                file_path.write_text('\n'.join(fixed_lines))
                print(f"✅ [GRPC] Fixed imports in {file_path.name}")
            except Exception as e:
                print(f"⚠️  [GRPC] Failed to fix imports in {file_path.name}: {e}")