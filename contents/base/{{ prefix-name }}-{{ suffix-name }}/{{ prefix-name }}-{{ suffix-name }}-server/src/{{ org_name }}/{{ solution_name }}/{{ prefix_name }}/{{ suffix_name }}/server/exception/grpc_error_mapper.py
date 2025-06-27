"""gRPC error mapping utilities."""

import grpc
import structlog

# Note: Import will work once we set up proper dependencies
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.api.exception.error_code import ErrorCode
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.api.exception.service_exception import ServiceException

logger = structlog.get_logger(__name__)


class GrpcErrorMapper:
    """Maps application exceptions to gRPC status codes and messages."""

    @staticmethod
    def map_service_exception_to_grpc_status(exception) -> grpc.StatusCode:
        """Map a ServiceException to the appropriate gRPC status code.
        
        Args:
            exception: ServiceException to map
            
        Returns:
            Appropriate gRPC status code
        """
        # This mapping will be implemented once we have the actual error codes
        error_code_mappings = {
            # Client errors (4xx equivalent)
            "INVALID_REQUEST": grpc.StatusCode.INVALID_ARGUMENT,
            "RESOURCE_NOT_FOUND": grpc.StatusCode.NOT_FOUND,
            "RESOURCE_ALREADY_EXISTS": grpc.StatusCode.ALREADY_EXISTS,
            "PERMISSION_DENIED": grpc.StatusCode.PERMISSION_DENIED,
            "AUTHENTICATION_FAILED": grpc.StatusCode.UNAUTHENTICATED,
            "RATE_LIMIT_EXCEEDED": grpc.StatusCode.RESOURCE_EXHAUSTED,
            "PRECONDITION_FAILED": grpc.StatusCode.FAILED_PRECONDITION,
            
            # Server errors (5xx equivalent)
            "INTERNAL_ERROR": grpc.StatusCode.INTERNAL,
            "SERVICE_UNAVAILABLE": grpc.StatusCode.UNAVAILABLE,
            "DATABASE_ERROR": grpc.StatusCode.INTERNAL,
            "EXTERNAL_SERVICE_ERROR": grpc.StatusCode.INTERNAL,
            "TIMEOUT": grpc.StatusCode.DEADLINE_EXCEEDED,
            
            # Validation errors
            "VALIDATION_ERROR": grpc.StatusCode.INVALID_ARGUMENT,
            "CONSTRAINT_VIOLATION": grpc.StatusCode.INVALID_ARGUMENT,
            
            # Business logic errors
            "BUSINESS_RULE_VIOLATION": grpc.StatusCode.FAILED_PRECONDITION,
            "OPERATION_NOT_ALLOWED": grpc.StatusCode.FAILED_PRECONDITION,
            
            # Unimplemented
            "NOT_IMPLEMENTED": grpc.StatusCode.UNIMPLEMENTED,
        }
        
        error_code_str = str(exception.error_code) if hasattr(exception, 'error_code') else "INTERNAL_ERROR"
        return error_code_mappings.get(error_code_str, grpc.StatusCode.INTERNAL)

    @staticmethod
    def create_grpc_error(exception) -> grpc.RpcError:
        """Create a gRPC error from a ServiceException.
        
        Args:
            exception: ServiceException to convert
            
        Returns:
            gRPC RpcError
        """
        status_code = GrpcErrorMapper.map_service_exception_to_grpc_status(exception)
        
        # Build error message
        message = str(exception)
        if hasattr(exception, 'correlation_id') and exception.correlation_id:
            message = f"{message} [correlation_id={exception.correlation_id}]"
        
        logger.error(
            "Converting ServiceException to gRPC error",
            error_code=str(exception.error_code) if hasattr(exception, 'error_code') else "unknown",
            grpc_status=status_code.name,
            message=message,
            correlation_id=getattr(exception, 'correlation_id', None),
            exc_info=True
        )
        
        return grpc.RpcError(status_code, message)

    @staticmethod
    def handle_unexpected_error(exception: Exception) -> grpc.RpcError:
        """Handle unexpected exceptions that are not ServiceExceptions.
        
        Args:
            exception: Unexpected exception
            
        Returns:
            gRPC RpcError with INTERNAL status
        """
        logger.error(
            "Handling unexpected error in gRPC service",
            exception_type=type(exception).__name__,
            message=str(exception),
            exc_info=True
        )
        
        # Don't leak internal details in production
        message = "An internal server error occurred"
        return grpc.RpcError(grpc.StatusCode.INTERNAL, message)


def grpc_exception_handler(func):
    """Decorator to handle exceptions in gRPC service methods.
    
    Args:
        func: The gRPC service method to wrap
        
    Returns:
        Wrapped function with exception handling
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if it's a ServiceException (will implement proper check later)
            if hasattr(e, 'error_code'):
                raise GrpcErrorMapper.create_grpc_error(e)
            else:
                raise GrpcErrorMapper.handle_unexpected_error(e)
    
    return wrapper