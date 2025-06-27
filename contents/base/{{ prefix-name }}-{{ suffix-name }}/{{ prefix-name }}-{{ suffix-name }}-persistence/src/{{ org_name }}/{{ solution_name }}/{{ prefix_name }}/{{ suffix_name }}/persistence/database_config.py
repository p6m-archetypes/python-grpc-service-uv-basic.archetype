"""Database configuration and session management."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool

from .models.base import Base


class DatabaseConfig:
    """Database configuration and session factory."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize database configuration.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.echo = echo
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Validate connections before use
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup.
        
        Yields:
            Async database session
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_session_no_autocommit(self) -> AsyncSession:
        """Get a database session without automatic commit/rollback.
        
        Returns:
            Async database session (caller responsible for commit/rollback)
        """
        return self.session_factory()

    async def close(self) -> None:
        """Close the database engine and all connections."""
        await self.engine.dispose()

    async def health_check(self) -> bool:
        """Perform a basic database health check.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            async with self.get_session() as session:
                # Simple query to test connectivity
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception:
            return False


# Global database instance (will be initialized by application)
db_config: DatabaseConfig = None


def get_db_config() -> DatabaseConfig:
    """Get the global database configuration instance.
    
    Returns:
        Database configuration instance
        
    Raises:
        RuntimeError: If database configuration not initialized
    """
    if db_config is None:
        raise RuntimeError("Database configuration not initialized. Call init_database() first.")
    return db_config


def init_database(database_url: str, echo: bool = False) -> DatabaseConfig:
    """Initialize the global database configuration.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        Initialized database configuration
    """
    global db_config
    db_config = DatabaseConfig(database_url, echo)
    return db_config


async def shutdown_database() -> None:
    """Shutdown the global database configuration."""
    global db_config
    if db_config:
        await db_config.close()
        db_config = None