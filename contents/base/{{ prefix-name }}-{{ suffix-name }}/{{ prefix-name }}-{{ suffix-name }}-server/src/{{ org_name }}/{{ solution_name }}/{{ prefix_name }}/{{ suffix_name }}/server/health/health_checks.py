"""Health check implementations for the Example Service."""

from abc import ABC, abstractmethod
from typing import Dict, List
import structlog

logger = structlog.get_logger(__name__)


class HealthCheck(ABC):
    """Base class for health checks."""
    
    @abstractmethod
    async def check(self) -> bool:
        """Perform the health check."""
        pass
    
    @property
    @abstractmethod 
    def name(self) -> str:
        """Name of the health check."""
        pass


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connectivity."""
    
    def __init__(self, db_config=None):
        self.db_config = db_config
    
    async def check(self) -> bool:
        """Check database connectivity."""
        if not self.db_config:
            return False
        # Placeholder implementation
        return True
    
    @property
    def name(self) -> str:
        return "database"


class GrpcHealthCheck(HealthCheck):
    """Health check for gRPC server."""
    
    def __init__(self, grpc_server=None):
        self.grpc_server = grpc_server
    
    async def check(self) -> bool:
        """Check gRPC server status."""
        # Placeholder implementation
        return self.grpc_server is not None
    
    @property
    def name(self) -> str:
        return "grpc"


class ExampleServiceHealthCheck(HealthCheck):
    """Health check for the example service."""
    
    def __init__(self, service_core=None):
        self.service_core = service_core
    
    async def check(self) -> bool:
        """Check service health."""
        # Placeholder implementation
        return True
    
    @property
    def name(self) -> str:
        return "{{ prefix_name }}_{{ suffix_name }}"


class HealthCheckManager:
    """Manages all health checks."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
    
    def add_check(self, check: HealthCheck) -> None:
        """Add a health check."""
        self.checks.append(check)
    
    def add_health_check(self, check: HealthCheck) -> None:
        """Add a health check (alias for add_check)."""
        self.add_check(check)
    
    async def check_all(self) -> Dict[str, bool]:
        """Run all health checks."""
        results = {}
        for check in self.checks:
            try:
                results[check.name] = await check.check()
            except Exception as e:
                logger.error(f"Health check {check.name} failed", error=str(e))
                results[check.name] = False
        return results
    
    async def is_healthy(self) -> bool:
        """Check if all health checks pass."""
        results = await self.check_all()
        return all(results.values())