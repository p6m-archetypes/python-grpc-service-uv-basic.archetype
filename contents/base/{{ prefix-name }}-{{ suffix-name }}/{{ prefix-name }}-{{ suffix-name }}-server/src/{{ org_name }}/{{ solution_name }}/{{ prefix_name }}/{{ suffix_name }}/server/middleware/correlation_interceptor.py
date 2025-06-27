"""gRPC interceptor for correlation ID management."""

import uuid
from typing import Any, Callable

import grpc
import structlog
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_context: ContextVar[str] = ContextVar('correlation_id', default='')

logger = structlog.get_logger(__name__)


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return correlation_id_context.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id_context.set(correlation_id)


class CorrelationIdInterceptor(grpc.aio.ServerInterceptor):
    """gRPC server interceptor for managing correlation IDs."""

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """Intercept gRPC calls to extract/generate correlation IDs.
        
        Args:
            continuation: The next interceptor or handler
            handler_call_details: Details about the handler call
            
        Returns:
            The result of the service call
        """
        # Extract correlation ID from metadata
        metadata = dict(handler_call_details.invocation_metadata)
        correlation_id = metadata.get('x-correlation-id')
        
        # Generate a new correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context
        set_correlation_id(correlation_id)
        
        # Add correlation ID to structured logging context
        logger.bind(correlation_id=correlation_id)
        
        logger.debug(
            "Processing gRPC request",
            method=handler_call_details.method,
            correlation_id=correlation_id
        )
        
        try:
            # Continue with the request
            response = await continuation(handler_call_details)
            return response
        except Exception as e:
            logger.error(
                "gRPC request failed",
                method=handler_call_details.method,
                correlation_id=correlation_id,
                error=str(e),
                exc_info=True
            )
            raise


class CorrelationIdClientInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """gRPC client interceptor for propagating correlation IDs."""

    async def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request
    ):
        """Intercept outgoing gRPC calls to add correlation ID.
        
        Args:
            continuation: The next interceptor or actual call
            client_call_details: Details about the client call
            request: The request message
            
        Returns:
            The response from the service
        """
        # Get current correlation ID
        correlation_id = get_correlation_id()
        
        if correlation_id:
            # Add correlation ID to metadata
            metadata = list(client_call_details.metadata or [])
            metadata.append(('x-correlation-id', correlation_id))
            
            # Create new call details with updated metadata
            new_details = client_call_details._replace(metadata=metadata)
            
            logger.debug(
                "Adding correlation ID to outgoing gRPC call",
                method=client_call_details.method,
                correlation_id=correlation_id
            )
            
            return await continuation(new_details, request)
        else:
            return await continuation(client_call_details, request)