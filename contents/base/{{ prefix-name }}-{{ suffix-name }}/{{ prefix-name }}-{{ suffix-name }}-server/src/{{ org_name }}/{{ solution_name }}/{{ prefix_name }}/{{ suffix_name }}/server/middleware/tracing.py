"""OpenTelemetry distributed tracing middleware for gRPC services."""

import logging
from typing import Any, Callable, Dict, Optional

import grpc
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    
    def __init__(
        self,
        service_name: str = "example-service-python",
        service_version: str = "0.1.0",
        otlp_endpoint: Optional[str] = None,
        jaeger_endpoint: Optional[str] = None,
        console_exporter: bool = False,
        sample_rate: float = 1.0,
        enable_grpc_instrumentation: bool = True,
        enable_sqlalchemy_instrumentation: bool = True,
        enable_asyncpg_instrumentation: bool = True,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        self.jaeger_endpoint = jaeger_endpoint
        self.console_exporter = console_exporter
        self.sample_rate = sample_rate
        self.enable_grpc_instrumentation = enable_grpc_instrumentation
        self.enable_sqlalchemy_instrumentation = enable_sqlalchemy_instrumentation
        self.enable_asyncpg_instrumentation = enable_asyncpg_instrumentation


def setup_tracing(config: TracingConfig) -> None:
    """Set up OpenTelemetry tracing with the specified configuration.
    
    Args:
        config: Tracing configuration
    """
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: config.service_version,
    })
    
    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Set up exporters
    if config.otlp_endpoint:
        # OTLP exporter for systems like Jaeger, Zipkin, or vendor solutions
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP tracing exporter configured for endpoint: {config.otlp_endpoint}")
    
    if config.jaeger_endpoint:
        # Jaeger exporter (if using Jaeger directly)
        try:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
                collector_endpoint=config.jaeger_endpoint,
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
            logger.info(f"Jaeger tracing exporter configured for endpoint: {config.jaeger_endpoint}")
        except ImportError:
            logger.warning("Jaeger exporter not available. Install with: pip install opentelemetry-exporter-jaeger")
    
    if config.console_exporter:
        # Console exporter for development (built into SDK)
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console tracing exporter configured")
    
    # Set up automatic instrumentation
    if config.enable_grpc_instrumentation:
        try:
            grpc_instrumentor = GrpcInstrumentorServer()
            grpc_instrumentor.instrument()
            logger.info("gRPC automatic instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to enable gRPC instrumentation: {e}")
    
    if config.enable_sqlalchemy_instrumentation:
        try:
            SQLAlchemyInstrumentor().instrument()
            logger.info("SQLAlchemy automatic instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to enable SQLAlchemy instrumentation: {e}")
    
    if config.enable_asyncpg_instrumentation:
        try:
            AsyncPGInstrumentor().instrument()
            logger.info("AsyncPG automatic instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to enable AsyncPG instrumentation: {e}")
    
    logger.info(f"OpenTelemetry tracing initialized for service: {config.service_name}")


class TracingInterceptor(grpc.aio.ServerInterceptor):
    """gRPC server interceptor that adds distributed tracing spans."""
    
    def __init__(self, tracer_name: str = "grpc-server"):
        self.tracer = trace.get_tracer(tracer_name)
    
    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Intercept gRPC service calls to add tracing spans."""
        method_name = handler_call_details.method
        
        # Extract trace context from incoming metadata
        metadata = dict(handler_call_details.invocation_metadata)
        context = extract(metadata)
        
        # Create span for this gRPC call
        with self.tracer.start_as_current_span(
            name=f"grpc.{method_name}",
            context=context,
            kind=trace.SpanKind.SERVER
        ) as span:
            try:
                # Add span attributes
                span.set_attribute(SpanAttributes.RPC_SYSTEM, "grpc")
                span.set_attribute(SpanAttributes.RPC_SERVICE, method_name.split('/')[1] if '/' in method_name else "unknown")
                span.set_attribute(SpanAttributes.RPC_METHOD, method_name.split('/')[-1] if '/' in method_name else method_name)
                span.set_attribute(SpanAttributes.RPC_GRPC_STATUS_CODE, grpc.StatusCode.OK.value[0])
                
                # Add correlation ID if present
                correlation_id = metadata.get("x-correlation-id")
                if correlation_id:
                    span.set_attribute("correlation.id", correlation_id)
                
                # Add user context if present
                user_id = metadata.get("x-user-id")
                if user_id:
                    span.set_attribute("user.id", user_id)
                
                # Inject trace context into outgoing metadata for downstream services
                carrier = {}
                inject(carrier)
                enhanced_metadata = list(handler_call_details.invocation_metadata)
                for key, value in carrier.items():
                    enhanced_metadata.append((key, value))
                
                # Create enhanced handler call details
                enhanced_handler_call_details = grpc.HandlerCallDetails(
                    method=handler_call_details.method,
                    invocation_metadata=enhanced_metadata
                )
                
                # Continue with the request
                handler = await continuation(enhanced_handler_call_details)
                
                # Wrap the handler to capture response information
                if hasattr(handler, 'unary_unary'):
                    original_handler = handler.unary_unary
                    
                    async def traced_unary_handler(request, context):
                        try:
                            span.add_event("request.received")
                            response = await original_handler(request, context)
                            span.add_event("response.sent")
                            span.set_status(Status(StatusCode.OK))
                            return response
                        except grpc.aio.AioRpcError as e:
                            span.set_attribute(SpanAttributes.RPC_GRPC_STATUS_CODE, e.code().value[0])
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                        except Exception as e:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                    
                    handler = handler._replace(unary_unary=traced_unary_handler)
                
                return handler
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.error(f"Error in tracing interceptor: {e}")
                raise


class TracingContextManager:
    """Context manager for custom tracing spans in business logic."""
    
    def __init__(self, tracer_name: str = "example-service"):
        self.tracer = trace.get_tracer(tracer_name)
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ):
        """Start a new tracing span.
        
        Args:
            name: Span name
            attributes: Optional span attributes
            kind: Span kind
            
        Returns:
            Span context manager
        """
        span = self.tracer.start_span(name=name, kind=kind)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    def get_current_span(self) -> Optional[trace.Span]:
        """Get the current active span."""
        return trace.get_current_span()
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the current span."""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the current span."""
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception) -> None:
        """Record an exception on the current span."""
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global tracing context manager instance
tracing = TracingContextManager()


def create_tracing_interceptor(tracer_name: str = "grpc-server") -> TracingInterceptor:
    """Factory function to create a tracing interceptor.
    
    Args:
        tracer_name: Name for the tracer
        
    Returns:
        Configured TracingInterceptor instance
    """
    return TracingInterceptor(tracer_name)