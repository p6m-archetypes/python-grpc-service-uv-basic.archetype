"""gRPC metrics interceptor for collecting request metrics."""

import time
from typing import Any, Callable, Optional

import grpc
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger(__name__)


class GrpcMetricsInterceptor(grpc.aio.ServerInterceptor):
    """gRPC server interceptor for collecting metrics."""

    def __init__(self) -> None:
        """Initialize the gRPC metrics interceptor."""
        
        # Request counters
        self.grpc_requests_total = Counter(
            'grpc_requests_total',
            'Total number of gRPC requests',
            ['method', 'status']
        )
        
        # Request duration histogram
        self.grpc_request_duration_seconds = Histogram(
            'grpc_request_duration_seconds',
            'Duration of gRPC requests in seconds',
            ['method'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Request size histogram
        self.grpc_request_size_bytes = Histogram(
            'grpc_request_size_bytes',
            'Size of gRPC request messages in bytes',
            ['method'],
            buckets=[64, 256, 1024, 4096, 16384, 65536, 262144, 1048576]
        )
        
        # Response size histogram
        self.grpc_response_size_bytes = Histogram(
            'grpc_response_size_bytes',
            'Size of gRPC response messages in bytes',
            ['method'],
            buckets=[64, 256, 1024, 4096, 16384, 65536, 262144, 1048576]
        )
        
        # Active requests gauge
        self.grpc_requests_active = Gauge(
            'grpc_requests_active',
            'Number of active gRPC requests',
            ['method']
        )
        
        logger.info("gRPC metrics interceptor initialized")

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """Intercept gRPC service calls to collect metrics.
        
        Args:
            continuation: The next interceptor or handler
            handler_call_details: Details about the handler call
            
        Returns:
            The result of the service call
        """
        method = handler_call_details.method
        start_time = time.time()
        
        # Extract method name for cleaner metrics
        method_name = method.split('/')[-1] if '/' in method else method
        
        # Increment active requests
        self.grpc_requests_active.labels(method=method_name).inc()
        
        logger.debug("gRPC request started", method=method_name)
        
        try:
            # Continue with the request
            response = await continuation(handler_call_details)
            
            # Record successful request
            duration = time.time() - start_time
            
            self.grpc_requests_total.labels(
                method=method_name,
                status='OK'
            ).inc()
            
            self.grpc_request_duration_seconds.labels(
                method=method_name
            ).observe(duration)
            
            logger.debug(
                "gRPC request completed successfully",
                method=method_name,
                duration_seconds=duration
            )
            
            return response
            
        except grpc.RpcError as e:
            # Record failed request with gRPC status
            duration = time.time() - start_time
            status_code = e.code().name if hasattr(e, 'code') else 'UNKNOWN'
            
            self.grpc_requests_total.labels(
                method=method_name,
                status=status_code
            ).inc()
            
            self.grpc_request_duration_seconds.labels(
                method=method_name
            ).observe(duration)
            
            logger.warning(
                "gRPC request failed",
                method=method_name,
                status=status_code,
                duration_seconds=duration,
                error=str(e)
            )
            
            raise
            
        except Exception as e:
            # Record failed request with generic error
            duration = time.time() - start_time
            
            self.grpc_requests_total.labels(
                method=method_name,
                status='INTERNAL'
            ).inc()
            
            self.grpc_request_duration_seconds.labels(
                method=method_name
            ).observe(duration)
            
            logger.error(
                "gRPC request failed with unexpected error",
                method=method_name,
                duration_seconds=duration,
                error=str(e),
                exc_info=True
            )
            
            raise
            
        finally:
            # Decrement active requests
            self.grpc_requests_active.labels(method=method_name).dec()

    def record_request_size(self, method: str, size_bytes: int) -> None:
        """Record the size of a request message.
        
        Args:
            method: The gRPC method name
            size_bytes: Size of the request in bytes
        """
        method_name = method.split('/')[-1] if '/' in method else method
        self.grpc_request_size_bytes.labels(method=method_name).observe(size_bytes)
        
        logger.debug(
            "Recorded request size",
            method=method_name,
            size_bytes=size_bytes
        )

    def record_response_size(self, method: str, size_bytes: int) -> None:
        """Record the size of a response message.
        
        Args:
            method: The gRPC method name
            size_bytes: Size of the response in bytes
        """
        method_name = method.split('/')[-1] if '/' in method else method
        self.grpc_response_size_bytes.labels(method=method_name).observe(size_bytes)
        
        logger.debug(
            "Recorded response size",
            method=method_name,
            size_bytes=size_bytes
        )


class GrpcClientMetrics:
    """Metrics collector for gRPC client operations."""

    def __init__(self) -> None:
        """Initialize gRPC client metrics."""
        
        # Client request counters
        self.grpc_client_requests_total = Counter(
            'grpc_client_requests_total',
            'Total number of gRPC client requests',
            ['method', 'status']
        )
        
        # Client request duration
        self.grpc_client_request_duration_seconds = Histogram(
            'grpc_client_request_duration_seconds',
            'Duration of gRPC client requests in seconds',
            ['method'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Active client requests
        self.grpc_client_requests_active = Gauge(
            'grpc_client_requests_active',
            'Number of active gRPC client requests',
            ['method']
        )

    def record_client_request_start(self, method: str) -> float:
        """Record the start of a client request.
        
        Args:
            method: The gRPC method name
            
        Returns:
            Start time for duration calculation
        """
        method_name = method.split('/')[-1] if '/' in method else method
        self.grpc_client_requests_active.labels(method=method_name).inc()
        
        logger.debug("gRPC client request started", method=method_name)
        return time.time()

    def record_client_request_success(self, method: str, start_time: float) -> None:
        """Record a successful client request.
        
        Args:
            method: The gRPC method name
            start_time: When the request started
        """
        method_name = method.split('/')[-1] if '/' in method else method
        duration = time.time() - start_time
        
        self.grpc_client_requests_total.labels(
            method=method_name,
            status='OK'
        ).inc()
        
        self.grpc_client_request_duration_seconds.labels(
            method=method_name
        ).observe(duration)
        
        self.grpc_client_requests_active.labels(method=method_name).dec()
        
        logger.debug(
            "gRPC client request completed successfully",
            method=method_name,
            duration_seconds=duration
        )

    def record_client_request_error(
        self, 
        method: str, 
        start_time: float, 
        status_code: str = 'UNKNOWN'
    ) -> None:
        """Record a failed client request.
        
        Args:
            method: The gRPC method name
            start_time: When the request started
            status_code: The gRPC status code
        """
        method_name = method.split('/')[-1] if '/' in method else method
        duration = time.time() - start_time
        
        self.grpc_client_requests_total.labels(
            method=method_name,
            status=status_code
        ).inc()
        
        self.grpc_client_request_duration_seconds.labels(
            method=method_name
        ).observe(duration)
        
        self.grpc_client_requests_active.labels(method=method_name).dec()
        
        logger.warning(
            "gRPC client request failed",
            method=method_name,
            status=status_code,
            duration_seconds=duration
        )


# Global instances
grpc_metrics_interceptor: Optional[GrpcMetricsInterceptor] = None
grpc_client_metrics: Optional[GrpcClientMetrics] = None


def get_grpc_metrics_interceptor() -> GrpcMetricsInterceptor:
    """Get the global gRPC metrics interceptor.
    
    Returns:
        gRPC metrics interceptor instance
    """
    global grpc_metrics_interceptor
    if grpc_metrics_interceptor is None:
        grpc_metrics_interceptor = GrpcMetricsInterceptor()
    return grpc_metrics_interceptor


def get_grpc_client_metrics() -> GrpcClientMetrics:
    """Get the global gRPC client metrics.
    
    Returns:
        gRPC client metrics instance
    """
    global grpc_client_metrics
    if grpc_client_metrics is None:
        grpc_client_metrics = GrpcClientMetrics()
    return grpc_client_metrics