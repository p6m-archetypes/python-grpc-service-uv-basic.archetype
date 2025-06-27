"""Configuration settings for the {{ PrefixName }} {{ SuffixName }} Service."""

import os
from typing import Optional


class DatabaseSettings:
    """Database configuration settings."""
    def __init__(self):
        self.url = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://postgres:postgres@localhost:5432/{{ prefix_name }}_{{ suffix_name }}"
        )
        self.echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        self.command_timeout = int(os.getenv("DATABASE_COMMAND_TIMEOUT", "30"))


class GrpcSettings:
    """gRPC server configuration settings."""
    def __init__(self):
        self.port = int(os.getenv("GRPC_PORT", "9010"))
        self.max_workers = int(os.getenv("GRPC_MAX_WORKERS", "10"))
        self.max_receive_message_length = int(os.getenv("GRPC_MAX_RECEIVE_MESSAGE_LENGTH", "4194304"))  # 4MB
        self.max_send_message_length = int(os.getenv("GRPC_MAX_SEND_MESSAGE_LENGTH", "4194304"))  # 4MB
        self.reflection_enabled = os.getenv("GRPC_REFLECTION_ENABLED", "true").lower() == "true"


class ManagementSettings:
    """Management server configuration settings."""
    def __init__(self):
        self.enabled = os.getenv("MANAGEMENT_ENABLED", "true").lower() == "true"
        self.port = int(os.getenv("MANAGEMENT_PORT", "8080"))


class ObservabilitySettings:
    """Observability configuration settings."""
    def __init__(self):
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")  # json or console
        
        # Metrics
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.metrics_endpoint = os.getenv("METRICS_ENDPOINT", "/metrics")
        
        # Tracing
        self.tracing_enabled = os.getenv("TRACING_ENABLED", "false").lower() == "true"
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT")
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
        self.trace_sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", "1.0"))
        
        # Health checks
        self.health_checks_enabled = os.getenv("HEALTH_CHECKS_ENABLED", "true").lower() == "true"


class AuthSettings:
    """Authentication and authorization settings."""
    def __init__(self):
        self.enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
        self.jwt_secret = os.getenv("JWT_SECRET", "default-secret-key")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.token_expiry = int(os.getenv("JWT_TOKEN_EXPIRY", "3600"))  # 1 hour


class Settings:
    """Main application settings."""
    def __init__(self):
        self.service_name = "{{ prefix-name }}-{{ suffix-name }}"
        self.version = "0.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.database = DatabaseSettings()
        self.grpc = GrpcSettings()
        self.management = ManagementSettings()
        self.observability = ObservabilitySettings()
        self.auth = AuthSettings()


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings