"""Business metrics collection for {{ PrefixName }} {{ SuffixName }} Service."""

import time
from typing import Dict, Optional

from prometheus_client import Counter, Histogram, Gauge, Info
import structlog

logger = structlog.get_logger(__name__)


class BusinessMetrics:
    """Collects business-specific metrics for the {{ PrefixName }} {{ SuffixName }} Service."""

    def __init__(self) -> None:
        """Initialize business metrics collectors."""
        
        # Request counters
        self.{{ prefix_name }}_operations_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_operations_total',
            'Total number of project prefix operations',
            ['operation', 'status']
        )
        
        # Request duration histograms
        self.{{ prefix_name }}_operation_duration_seconds = Histogram(
            '{{ prefix_name }}_{{ suffix_name }}_operation_duration_seconds',
            'Duration of project prefix operations in seconds',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Active project prefixes gauge
        self.active_{{ prefix_name }}es_total = Gauge(
            '{{ prefix_name }}_{{ suffix_name }}_active_entities_total',
            'Total number of active project prefix entities in the system'
        )
        
        # Database operation metrics
        self.database_operations_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_database_operations_total',
            'Total number of database operations',
            ['operation', 'table', 'status']
        )
        
        self.database_operation_duration_seconds = Histogram(
            '{{ prefix_name }}_{{ suffix_name }}_database_operation_duration_seconds',
            'Duration of database operations in seconds',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        # Connection pool metrics
        self.database_connections_active = Gauge(
            '{{ prefix_name }}_{{ suffix_name }}_database_connections_active',
            'Number of active database connections'
        )
        
        self.database_connections_idle = Gauge(
            '{{ prefix_name }}_{{ suffix_name }}_database_connections_idle',
            'Number of idle database connections'
        )
        
        # Error metrics
        self.operation_errors_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_errors_total',
            'Total number of errors by type',
            ['error_code', 'operation']
        )
        
        # Validation and authorization metrics (matching .NET)
        self.validation_errors_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_validation_errors_total',
            'Total number of validation errors',
            ['field', 'error_type']
        )
        
        self.authorization_failures_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_authorization_failures_total',
            'Total number of authorization failures',
            ['operation', 'reason']
        )
        
        # Entity operation counters (matching .NET pattern)
        self.entities_created_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_entities_created_total',
            'Total number of entities created',
            ['entity_type']
        )
        
        self.entities_updated_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_entities_updated_total',
            'Total number of entities updated',
            ['entity_type']
        )
        
        self.entities_deleted_total = Counter(
            '{{ prefix_name }}_{{ suffix_name }}_entities_deleted_total',
            'Total number of entities deleted',
            ['entity_type']
        )
        
        # Service info
        self.service_info = Info(
            '{{ prefix_name }}_{{ suffix_name }}_service_info',
            'Information about the {{ PrefixName }} {{ SuffixName }} Service'
        )
        
        # Initialize service info
        self.service_info.info({
            'version': '0.1.0',
            'service': '{{ prefix-name }}-{{ suffix-name }}',
            'environment': 'development'
        })

    def record_operation_start(self, operation: str) -> float:
        """Record the start of an operation.
        
        Args:
            operation: The operation name
            
        Returns:
            Start time for duration calculation
        """
        logger.debug("Recording operation start", operation=operation)
        return time.time()

    def record_operation_success(self, operation: str, start_time: float) -> None:
        """Record a successful operation.
        
        Args:
            operation: The operation name
            start_time: When the operation started
        """
        duration = time.time() - start_time
        
        self.example_operations_total.labels(
            operation=operation,
            status='success'
        ).inc()
        
        self.example_operation_duration_seconds.labels(
            operation=operation
        ).observe(duration)
        
        logger.debug(
            "Recorded successful operation",
            operation=operation,
            duration_seconds=duration
        )

    def record_operation_error(self, operation: str, start_time: float, error_code: str) -> None:
        """Record a failed operation.
        
        Args:
            operation: The operation name
            start_time: When the operation started
            error_code: The error code
        """
        duration = time.time() - start_time
        
        self.example_operations_total.labels(
            operation=operation,
            status='error'
        ).inc()
        
        self.example_operation_duration_seconds.labels(
            operation=operation
        ).observe(duration)
        
        self.example_errors_total.labels(
            error_code=error_code,
            operation=operation
        ).inc()
        
        logger.debug(
            "Recorded failed operation",
            operation=operation,
            error_code=error_code,
            duration_seconds=duration
        )

    def record_database_operation_start(self, operation: str, table: str) -> float:
        """Record the start of a database operation.
        
        Args:
            operation: The database operation (select, insert, update, delete)
            table: The table name
            
        Returns:
            Start time for duration calculation
        """
        logger.debug(
            "Recording database operation start",
            operation=operation,
            table=table
        )
        return time.time()

    def record_database_operation_success(
        self, 
        operation: str, 
        table: str, 
        start_time: float
    ) -> None:
        """Record a successful database operation.
        
        Args:
            operation: The database operation
            table: The table name
            start_time: When the operation started
        """
        duration = time.time() - start_time
        
        self.database_operations_total.labels(
            operation=operation,
            table=table,
            status='success'
        ).inc()
        
        self.database_operation_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
        
        logger.debug(
            "Recorded successful database operation",
            operation=operation,
            table=table,
            duration_seconds=duration
        )

    def record_database_operation_error(
        self, 
        operation: str, 
        table: str, 
        start_time: float
    ) -> None:
        """Record a failed database operation.
        
        Args:
            operation: The database operation
            table: The table name
            start_time: When the operation started
        """
        duration = time.time() - start_time
        
        self.database_operations_total.labels(
            operation=operation,
            table=table,
            status='error'
        ).inc()
        
        self.database_operation_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
        
        logger.debug(
            "Recorded failed database operation",
            operation=operation,
            table=table,
            duration_seconds=duration
        )

    def set_active_examples_count(self, count: int) -> None:
        """Set the current count of active examples.
        
        Args:
            count: Number of active examples
        """
        self.active_examples_total.set(count)
        logger.debug("Updated active examples count", count=count)

    def set_database_connection_counts(self, active: int, idle: int) -> None:
        """Set the current database connection counts.
        
        Args:
            active: Number of active connections
            idle: Number of idle connections
        """
        self.database_connections_active.set(active)
        self.database_connections_idle.set(idle)
        
        logger.debug(
            "Updated database connection counts",
            active=active,
            idle=idle
        )

    def get_metrics_summary(self) -> Dict[str, float]:
        """Get a summary of current metric values.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            'active_examples': self.active_examples_total._value._value,
            'database_connections_active': self.database_connections_active._value._value,
            'database_connections_idle': self.database_connections_idle._value._value,
        }


# Global metrics instance
business_metrics: Optional[BusinessMetrics] = None


def get_business_metrics() -> BusinessMetrics:
    """Get the global business metrics instance.
    
    Returns:
        Business metrics instance
    """
    global business_metrics
    if business_metrics is None:
        business_metrics = BusinessMetrics()
    return business_metrics


def init_business_metrics() -> BusinessMetrics:
    """Initialize the global business metrics instance.
    
    Returns:
        Initialized business metrics instance
    """
    global business_metrics
    business_metrics = BusinessMetrics()
    logger.info("Business metrics initialized")
    return business_metrics