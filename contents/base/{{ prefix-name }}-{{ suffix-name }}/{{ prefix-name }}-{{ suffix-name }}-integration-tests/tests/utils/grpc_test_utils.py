"""Utilities for gRPC testing."""

import asyncio
from typing import AsyncGenerator, Optional

import grpc
import pytest
from grpc import aio
from grpc_testing import server_from_dictionary, strict_real_time

# Note: These imports will work once we set up proper proto generation
# import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2_grpc as pb2_grpc
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.server.grpc.example_service_grpc_impl import ExampleServiceGrpcImpl


class GrpcTestServer:
    """Test server for gRPC service testing."""

    def __init__(self, service_impl, port: int = 0):
        """Initialize the test gRPC server.
        
        Args:
            service_impl: gRPC service implementation
            port: Port to bind to (0 for auto-assigned)
        """
        self.service_impl = service_impl
        self.port = port
        self.server: Optional[aio.Server] = None
        self.actual_port: Optional[int] = None

    async def start(self) -> int:
        """Start the test gRPC server.
        
        Returns:
            The actual port the server is listening on
        """
        self.server = aio.server()
        
        # Add service implementation
        # This will be implemented once we have actual protobuf classes
        # pb2_grpc.add_{{ PrefixName }}{{ SuffixName }}Servicer_to_server(self.service_impl, self.server)
        
        # Bind to port
        listen_addr = f'localhost:{self.port}'
        self.actual_port = self.server.add_insecure_port(listen_addr)
        
        # Start server
        await self.server.start()
        
        return self.actual_port

    async def stop(self) -> None:
        """Stop the test gRPC server."""
        if self.server:
            await self.server.stop(grace=5)
            self.server = None

    async def __aenter__(self) -> "GrpcTestServer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()


class GrpcTestClient:
    """Test client for gRPC service testing."""

    def __init__(self, host: str = "localhost", port: int = None):
        """Initialize the test gRPC client.
        
        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.channel: Optional[aio.Channel] = None
        self.stub = None

    async def connect(self) -> None:
        """Connect to the gRPC server."""
        if self.port is None:
            raise ValueError("Port must be specified")
        
        # Create channel
        self.channel = aio.insecure_channel(f"{self.host}:{self.port}")
        
        # Create stub
        # This will be implemented once we have actual protobuf classes
        # self.stub = pb2_grpc.{{ PrefixName }}{{ SuffixName }}Stub(self.channel)

    async def disconnect(self) -> None:
        """Disconnect from the gRPC server."""
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None

    async def __aenter__(self) -> "GrpcTestClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()


@pytest.fixture
async def grpc_test_server(example_service_core) -> AsyncGenerator[GrpcTestServer, None]:
    """Create a test gRPC server."""
    # This will be implemented once we have actual service implementation
    # service_impl = ExampleServiceGrpcImpl(example_service_core)
    service_impl = type('ServiceImpl', (), {})()
    
    async with GrpcTestServer(service_impl) as server:
        yield server


@pytest.fixture
async def grpc_test_client(grpc_test_server: GrpcTestServer) -> AsyncGenerator[GrpcTestClient, None]:
    """Create a test gRPC client connected to the test server."""
    client = GrpcTestClient(port=grpc_test_server.actual_port)
    async with client:
        yield client


class MockGrpcContext:
    """Mock gRPC context for unit testing."""

    def __init__(self, metadata: dict = None):
        """Initialize the mock context.
        
        Args:
            metadata: Request metadata
        """
        self._metadata = metadata or {}
        self._code = None
        self._details = None

    def invocation_metadata(self):
        """Return request metadata."""
        return [(key, value) for key, value in self._metadata.items()]

    def set_code(self, code):
        """Set response code."""
        self._code = code

    def set_details(self, details):
        """Set response details."""
        self._details = details

    def abort(self, code, details):
        """Abort the request."""
        self._code = code
        self._details = details
        raise grpc.RpcError(f"gRPC call failed: {code} - {details}")


@pytest.fixture
def mock_grpc_context():
    """Create a mock gRPC context."""
    return MockGrpcContext()


@pytest.fixture
def mock_grpc_context_with_correlation_id():
    """Create a mock gRPC context with correlation ID."""
    return MockGrpcContext(metadata={"x-correlation-id": "test-correlation-id"})


def create_grpc_error(code: grpc.StatusCode, message: str) -> grpc.RpcError:
    """Create a gRPC error for testing.
    
    Args:
        code: gRPC status code
        message: Error message
        
    Returns:
        gRPC RpcError
    """
    return grpc.RpcError(code, message)


class GrpcTestUtils:
    """Utility methods for gRPC testing."""
    
    @staticmethod
    def assert_grpc_error(expected_code: grpc.StatusCode, expected_message: str = None):
        """Context manager to assert that a gRPC error is raised.
        
        Args:
            expected_code: Expected gRPC status code
            expected_message: Expected error message (optional)
        """
        return pytest.raises(grpc.RpcError, match=expected_message if expected_message else None)
    
    @staticmethod
    async def wait_for_server_ready(channel: aio.Channel, timeout: float = 10.0) -> bool:
        """Wait for gRPC server to be ready.
        
        Args:
            channel: gRPC channel
            timeout: Timeout in seconds
            
        Returns:
            True if server is ready, False if timeout
        """
        try:
            await asyncio.wait_for(
                grpc.channel_ready_future(channel),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False
    
    @staticmethod
    def create_test_metadata(correlation_id: str = None, **kwargs) -> list:
        """Create test metadata for gRPC calls.
        
        Args:
            correlation_id: Correlation ID
            **kwargs: Additional metadata
            
        Returns:
            List of metadata tuples
        """
        metadata = []
        
        if correlation_id:
            metadata.append(("x-correlation-id", correlation_id))
        
        for key, value in kwargs.items():
            metadata.append((key, str(value)))
        
        return metadata


@pytest.fixture
def grpc_test_utils():
    """Provide access to GrpcTestUtils."""
    return GrpcTestUtils