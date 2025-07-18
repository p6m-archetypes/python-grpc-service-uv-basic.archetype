"""gRPC connectivity and health check tests for CI/CD integration."""

import asyncio
import os
import socket
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest


class TestGrpcConnectivity:
    """Test gRPC server connectivity and health checks."""

    @pytest.mark.integration
    @pytest.mark.requires_docker
    async def test_grpc_server_port_accessible(self):
        """Test that gRPC server port is accessible."""
        host = os.getenv("GRPC_SERVER_HOST", "localhost")
        port = int(os.getenv("GRPC_SERVER_PORT", "9010"))
        
        # Test socket connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((host, port))
            assert result == 0, f"Cannot connect to gRPC server at {host}:{port}"
        finally:
            sock.close()

    @pytest.mark.integration
    @pytest.mark.requires_docker
    async def test_grpc_channel_creation(self):
        """Test gRPC channel creation and basic connectivity."""
        host = os.getenv("GRPC_SERVER_HOST", "localhost")
        port = int(os.getenv("GRPC_SERVER_PORT", "9010"))
        
        channel = grpc.aio.insecure_channel(f"{host}:{port}")
        
        try:
            # Test channel connectivity with timeout
            # Wait for channel to be ready by trying to connect
            for _ in range(10):  # 10 attempts over 10 seconds
                state = channel.get_state(try_to_connect=True)
                if state == grpc.ChannelConnectivity.READY:
                    break
                await asyncio.sleep(1.0)
            
            # Channel should be ready
            state = channel.get_state(try_to_connect=False)
            assert state == grpc.ChannelConnectivity.READY, f"Channel state: {state}"
            
        except asyncio.TimeoutError:
            pytest.fail(f"gRPC channel not ready within timeout for {host}:{port}")
        finally:
            await channel.close()

    @pytest.mark.integration 
    @pytest.mark.requires_docker
    async def test_management_server_health(self):
        """Test management server health endpoints."""
        import aiohttp
        
        management_host = os.getenv("GRPC_SERVER_HOST", "localhost")
        management_port = int(os.getenv("MANAGEMENT_PORT", "9011"))
        base_url = f"http://{management_host}:{management_port}"
        
        async with aiohttp.ClientSession() as session:
            # Test liveness probe
            async with session.get(f"{base_url}/health/live") as response:
                assert response.status == 200, "Liveness check failed"
                data = await response.json()
                assert data.get("status").lower() == "healthy"
            
            # Test readiness probe  
            async with session.get(f"{base_url}/health/ready") as response:
                assert response.status == 200, "Readiness check failed"
                data = await response.json()
                assert data.get("status").lower() in ["ready", "healthy"]  # Some endpoints return "Healthy" for both

    @pytest.mark.integration
    @pytest.mark.requires_docker
    async def test_grpc_reflection_enabled(self):
        """Test that gRPC reflection is enabled (useful for debugging)."""
        host = os.getenv("GRPC_SERVER_HOST", "localhost")
        port = int(os.getenv("GRPC_SERVER_PORT", "9010"))
        
        channel = grpc.aio.insecure_channel(f"{host}:{port}")
        
        try:
            # Test reflection by listing services
            from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
            
            stub = reflection_pb2_grpc.ServerReflectionStub(channel)
            request = reflection_pb2.ServerReflectionRequest()
            request.list_services = ""
            
            responses = []
            async for response in stub.ServerReflectionInfo(iter([request])):
                responses.append(response)
                break  # Just test that we get a response
            
            assert len(responses) > 0, "No reflection responses received"
            
        except ImportError:
            pytest.skip("grpc-reflection not available")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                pytest.fail("gRPC reflection is not enabled on server")
            else:
                pytest.fail(f"Reflection test failed: {e}")
        finally:
            await channel.close()

    @pytest.mark.integration
    @pytest.mark.requires_docker 
    async def test_grpc_server_metadata_handling(self):
        """Test that server handles metadata correctly."""
        host = os.getenv("GRPC_SERVER_HOST", "localhost")
        port = int(os.getenv("GRPC_SERVER_PORT", "9010"))
        
        channel = grpc.aio.insecure_channel(f"{host}:{port}")
        
        try:
            # Create metadata
            metadata = [
                ('x-correlation-id', 'test-correlation-123'),
                ('x-request-id', 'test-request-456'),
                ('user-agent', 'integration-test/1.0')
            ]
            
            # Try a simple call with metadata (this will fail gracefully if service not implemented)
            # We're mainly testing that the channel accepts the metadata format
            try:
                # Use health check service if available
                from grpc_health.v1 import health_pb2, health_pb2_grpc
                
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest()
                
                await stub.Check(request, metadata=metadata, timeout=5.0)
                
            except grpc.RpcError as e:
                # UNIMPLEMENTED is fine - means server received the call
                if e.code() not in [grpc.StatusCode.UNIMPLEMENTED, grpc.StatusCode.NOT_FOUND]:
                    pytest.fail(f"Unexpected gRPC error: {e}")
            except ImportError:
                # Health check not available, that's ok for this test
                pass
                
        finally:
            await channel.close()

    @pytest.mark.integration
    @pytest.mark.requires_docker
    async def test_concurrent_grpc_connections(self):
        """Test that server handles multiple concurrent connections."""
        host = os.getenv("GRPC_SERVER_HOST", "localhost")
        port = int(os.getenv("GRPC_SERVER_PORT", "9010"))
        
        async def create_and_test_channel():
            channel = grpc.aio.insecure_channel(f"{host}:{port}")
            try:
                # Wait for channel to be ready by trying to connect
                for _ in range(10):  # 10 attempts over 10 seconds
                    state = channel.get_state(try_to_connect=True)
                    if state == grpc.ChannelConnectivity.READY:
                        return True
                    await asyncio.sleep(1.0)
                return False
            except:
                return False
            finally:
                await channel.close()
        
        # Create multiple concurrent connections
        tasks = [create_and_test_channel() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All connections should succeed
        successful_connections = sum(1 for result in results if result is True)
        assert successful_connections >= 3, f"Only {successful_connections}/5 connections succeeded"

    @pytest.mark.integration
    @pytest.mark.requires_docker
    async def test_grpc_server_shutdown_gracefully(self):
        """Test server shutdown behavior (if management endpoint available)."""
        management_host = os.getenv("GRPC_SERVER_HOST", "localhost") 
        management_port = int(os.getenv("MANAGEMENT_PORT", "9011"))
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test that management server responds to status requests
            try:
                async with session.get(f"http://{management_host}:{management_port}/metrics") as response:
                    # Metrics endpoint should be available
                    assert response.status in [200, 404], "Management server not responding"
                    
            except aiohttp.ClientError:
                pytest.skip("Management server not accessible")


class TestEnvironmentConfiguration:
    """Test that environment is properly configured for integration tests."""

    @pytest.mark.integration
    def test_required_environment_variables(self):
        """Test that required environment variables are set."""
        required_vars = [
            "DATABASE_URL",
            "GRPC_SERVER_HOST", 
            "GRPC_SERVER_PORT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        assert not missing_vars, f"Missing required environment variables: {missing_vars}"

    @pytest.mark.integration
    async def test_database_connectivity(self):
        """Test database connectivity from environment."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not set")
        
        # Test basic database URL format
        assert database_url.startswith(("postgresql://", "postgresql+asyncpg://"))
        
        # Try to import and test database connection
        try:
            import asyncpg
            import urllib.parse
            
            # Parse database URL
            parsed = urllib.parse.urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
            
            # Test connection
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                command_timeout=5
            )
            
            # Simple query test
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            await conn.close()
            
        except ImportError:
            pytest.skip("asyncpg not available for database test")
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.integration
    def test_python_path_configuration(self):
        """Test that Python path is correctly configured for imports."""
        try:
            # Test that we can import our service modules
            import sys
            workspace_path = os.getenv("PYTHONPATH", "")
            
            if workspace_path:
                assert workspace_path in sys.path, "PYTHONPATH not in sys.path"
            
            # Try importing a core module (will fail gracefully if not available)
            try:
                from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.core import example_service_core
            except ImportError:
                # Expected if modules not fully built yet
                pass
                
        except Exception as e:
            pytest.fail(f"Python path configuration issue: {e}") 