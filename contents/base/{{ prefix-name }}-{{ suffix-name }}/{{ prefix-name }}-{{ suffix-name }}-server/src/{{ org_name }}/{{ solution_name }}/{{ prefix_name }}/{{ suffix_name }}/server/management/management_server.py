"""Management HTTP server for health checks, metrics, and administration."""

from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

from ..health.health_checks import HealthCheckManager, HealthStatus
from ..metrics.business_metrics import get_business_metrics

logger = structlog.get_logger(__name__)


def create_management_app(
    health_check_manager: HealthCheckManager,
    settings: Any
) -> FastAPI:
    """Create the management FastAPI application.
    
    Args:
        health_check_manager: Health check manager instance
        settings: Application settings
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Example Service Management",
        description="Management endpoints for Example Service",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )

    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint with service information."""
        return {
            "service": settings.name,
            "version": settings.version,
            "environment": settings.environment,
            "status": "running"
        }

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Comprehensive health check endpoint."""
        try:
            health_results = await health_check_manager.check_all_health()
            overall_status = await health_check_manager.get_overall_status()
            
            # Convert health results to serializable format
            serializable_results = {}
            for name, result in health_results.items():
                serializable_results[name] = {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "duration_ms": result.duration_ms
                }
            
            response_data = {
                "status": overall_status.value,
                "checks": serializable_results,
                "timestamp": time.time()
            }
            
            # Set HTTP status based on health
            if overall_status == HealthStatus.UP:
                return response_data
            else:
                raise HTTPException(status_code=503, detail=response_data)
                
        except Exception as e:
            logger.error("Health check failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "DOWN",
                    "error": str(e),
                    "timestamp": time.time()
                }
            )

    @app.get("/health/live")
    async def liveness_check() -> Dict[str, str]:
        """Kubernetes liveness probe endpoint."""
        # Simple liveness check - service is running
        return {"status": "UP"}

    @app.get("/health/ready")
    async def readiness_check() -> Dict[str, Any]:
        """Kubernetes readiness probe endpoint."""
        try:
            overall_status = await health_check_manager.get_overall_status()
            
            if overall_status == HealthStatus.UP:
                return {"status": "UP"}
            else:
                raise HTTPException(
                    status_code=503,
                    detail={"status": "DOWN"}
                )
        except Exception as e:
            logger.error("Readiness check failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={"status": "DOWN", "error": str(e)}
            )

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        try:
            # Update dynamic metrics before exposing
            await _update_dynamic_metrics()
            
            # Generate Prometheus metrics
            metrics_data = generate_latest()
            
            return Response(
                content=metrics_data,
                media_type=CONTENT_TYPE_LATEST
            )
            
        except Exception as e:
            logger.error("Failed to generate metrics", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to generate metrics")

    @app.get("/metrics/business")
    async def business_metrics() -> Dict[str, Any]:
        """Business metrics in JSON format."""
        try:
            business_metrics = get_business_metrics()
            summary = business_metrics.get_metrics_summary()
            
            return {
                "timestamp": time.time(),
                "metrics": summary
            }
            
        except Exception as e:
            logger.error("Failed to get business metrics", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get business metrics")

    @app.get("/info")
    async def service_info() -> Dict[str, Any]:
        """Service information endpoint."""
        return {
            "service": {
                "name": settings.name,
                "version": settings.version,
                "environment": settings.environment,
                "debug": settings.debug
            },
            "configuration": {
                "grpc": {
                    "port": settings.grpc.port,
                    "reflection_enabled": settings.grpc.reflection_enabled,
                    "max_workers": settings.grpc.max_workers
                },
                "database": {
                    "echo": settings.database.echo,
                    "pool_size": settings.database.pool_size
                },
                "logging": {
                    "level": settings.logging.level,
                    "format": settings.logging.format
                }
            },
            "timestamp": time.time()
        }

    @app.get("/debug/config")
    async def debug_config() -> Dict[str, Any]:
        """Debug endpoint for configuration (only available in debug mode)."""
        if not settings.debug:
            raise HTTPException(status_code=404, detail="Not found")
        
        # Return configuration without sensitive data
        return {
            "settings": {
                "name": settings.name,
                "version": settings.version,
                "environment": settings.environment,
                "debug": settings.debug,
                "grpc": {
                    "port": settings.grpc.port,
                    "reflection_enabled": settings.grpc.reflection_enabled,
                    "max_workers": settings.grpc.max_workers,
                    "max_receive_message_length": settings.grpc.max_receive_message_length,
                    "max_send_message_length": settings.grpc.max_send_message_length
                },
                "management": {
                    "port": settings.management.port,
                    "enabled": settings.management.enabled
                },
                "logging": {
                    "level": settings.logging.level,
                    "format": settings.logging.format,
                    "include_trace": settings.logging.include_trace
                },
                "metrics": {
                    "enabled": settings.metrics.enabled,
                    "prometheus_enabled": settings.metrics.prometheus_enabled
                }
            }
        }

    @app.post("/admin/log-level")
    async def set_log_level(request: Dict[str, str]) -> Dict[str, str]:
        """Change the logging level at runtime."""
        if not settings.debug:
            raise HTTPException(status_code=404, detail="Not found")
        
        level = request.get("level", "").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        if level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid log level. Must be one of: {valid_levels}"
            )
        
        # Update logging level
        import logging
        logging.getLogger().setLevel(level)
        
        logger.info("Log level changed", new_level=level)
        
        return {"status": "success", "level": level}

    # Add exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for management endpoints."""
        logger.error(
            "Unhandled exception in management endpoint",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        return HTTPException(
            status_code=500,
            detail="Internal server error"
        )

    logger.info("Management server application created")
    return app


async def _update_dynamic_metrics() -> None:
    """Update dynamic metrics before exposing them."""
    try:
        # This would update metrics that need to be refreshed
        # For example, current counts from the database
        
        # business_metrics = get_business_metrics()
        # 
        # # Update active examples count
        # with get_db_config().get_session() as session:
        #     count = await session.execute("SELECT COUNT(*) FROM example")
        #     business_metrics.set_active_examples_count(count.scalar())
        # 
        # # Update connection pool metrics
        # pool = get_db_config().engine.pool
        # business_metrics.set_database_connection_counts(
        #     active=pool.checkedout(),
        #     idle=pool.size() - pool.checkedout()
        # )
        
        pass  # Placeholder until we have actual database integration
        
    except Exception as e:
        logger.warning("Failed to update dynamic metrics", error=str(e))


# Import time for timestamps
import time