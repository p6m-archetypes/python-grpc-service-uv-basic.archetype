"""Circuit breaker pattern implementation for resilient service calls."""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for protecting against cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type that counts as failure
            name: Name for logging and identification
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original function exceptions
        """
        async with self._lock:
            # Check if circuit should transition to half-open
            if self.state == CircuitState.OPEN and self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(
                    "Circuit breaker transitioning to half-open",
                    circuit_name=self.name
                )

            # If circuit is open, reject the request
            if self.state == CircuitState.OPEN:
                logger.warning(
                    "Circuit breaker is open, rejecting request",
                    circuit_name=self.name,
                    failure_count=self.failure_count
                )
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open"
                )

        # Execute the function
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout

    async def _on_success(self):
        """Handle successful function execution."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                # After a few successes, close the circuit
                if self.success_count >= 3:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.last_failure_time = None
                    logger.info(
                        "Circuit breaker closed after successful recovery",
                        circuit_name=self.name
                    )
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self):
        """Handle failed function execution."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Failed during half-open, go back to open
                self.state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker failed during half-open, returning to open",
                    circuit_name=self.name,
                    failure_count=self.failure_count
                )
            elif (self.state == CircuitState.CLOSED and 
                  self.failure_count >= self.failure_threshold):
                # Too many failures, open the circuit
                self.state = CircuitState.OPEN
                logger.error(
                    "Circuit breaker opened due to failure threshold",
                    circuit_name=self.name,
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold
                )

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    async def reset(self):
        """Manually reset the circuit breaker to closed state."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.success_count = 0
            logger.info("Circuit breaker manually reset", circuit_name=self.name)

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout": self.timeout
        }


class DatabaseCircuitBreaker(CircuitBreaker):
    """Circuit breaker specifically for database operations."""

    def __init__(self, name: str = "database"):
        """Initialize database circuit breaker with appropriate settings."""
        super().__init__(
            failure_threshold=3,  # Lower threshold for database
            timeout=30.0,         # Shorter timeout for database recovery
            expected_exception=Exception,  # Catch all database exceptions
            name=name
        )


class ExternalServiceCircuitBreaker(CircuitBreaker):
    """Circuit breaker for external service calls."""

    def __init__(self, service_name: str):
        """Initialize external service circuit breaker.
        
        Args:
            service_name: Name of the external service
        """
        super().__init__(
            failure_threshold=5,  # More tolerant of external service failures
            timeout=60.0,         # Longer recovery time for external services
            expected_exception=Exception,
            name=f"external_service_{service_name}"
        )


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            **kwargs: Circuit breaker configuration
            
        Returns:
            Circuit breaker instance
        """
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name, **kwargs)
                logger.info("Created new circuit breaker", name=name)
            return self._breakers[name]

    async def get_database_breaker(self, db_name: str = "default") -> DatabaseCircuitBreaker:
        """Get or create a database circuit breaker.
        
        Args:
            db_name: Database name
            
        Returns:
            Database circuit breaker instance
        """
        name = f"database_{db_name}"
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = DatabaseCircuitBreaker(name)
                logger.info("Created new database circuit breaker", name=name)
            return self._breakers[name]

    async def get_external_service_breaker(self, service_name: str) -> ExternalServiceCircuitBreaker:
        """Get or create an external service circuit breaker.
        
        Args:
            service_name: External service name
            
        Returns:
            External service circuit breaker instance
        """
        name = f"external_service_{service_name}"
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = ExternalServiceCircuitBreaker(service_name)
                logger.info("Created new external service circuit breaker", name=name)
            return self._breakers[name]

    def get_all_stats(self) -> list[dict]:
        """Get statistics for all circuit breakers.
        
        Returns:
            List of circuit breaker statistics
        """
        return [breaker.get_stats() for breaker in self._breakers.values()]

    async def reset_all(self):
        """Reset all circuit breakers."""
        async with self._lock:
            for breaker in self._breakers.values():
                await breaker.reset()
            logger.info("Reset all circuit breakers")


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()


async def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get a circuit breaker from the global registry.
    
    Args:
        name: Circuit breaker name
        **kwargs: Circuit breaker configuration
        
    Returns:
        Circuit breaker instance
    """
    return await circuit_breaker_registry.get_breaker(name, **kwargs)


async def get_database_circuit_breaker(db_name: str = "default") -> DatabaseCircuitBreaker:
    """Get a database circuit breaker from the global registry.
    
    Args:
        db_name: Database name
        
    Returns:
        Database circuit breaker instance
    """
    return await circuit_breaker_registry.get_database_breaker(db_name)