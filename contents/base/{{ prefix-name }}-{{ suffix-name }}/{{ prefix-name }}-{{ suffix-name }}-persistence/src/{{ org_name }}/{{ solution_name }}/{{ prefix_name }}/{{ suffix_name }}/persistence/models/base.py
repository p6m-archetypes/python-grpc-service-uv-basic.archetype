"""Base classes for database entities with common patterns."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database entities."""
    pass


class AbstractEntity(Base):
    """Abstract base entity with common fields."""
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )


class AbstractCreated(AbstractEntity):
    """Abstract entity with creation timestamp."""
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


class AbstractModified(Base):
    """Abstract mixin for entities with modification timestamp."""
    __abstract__ = True

    modified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )


class AbstractCreatedModified(AbstractCreated, AbstractModified):
    """Abstract entity with both creation and modification timestamps."""
    __abstract__ = True


class AbstractVersioned(Base):
    """Abstract mixin for entities with version control."""
    __abstract__ = True

    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )


class AbstractCreatedModifiedVersioned(AbstractCreatedModified, AbstractVersioned):
    """Abstract entity with timestamps and version control."""
    __abstract__ = True


class AbstractIdentifiableCreatedModifiedVersioned(AbstractCreatedModifiedVersioned):
    """Abstract entity with ID, timestamps, and version control."""
    __abstract__ = True


class AbstractLookupEntity(AbstractCreatedModifiedVersioned):
    """Abstract entity for lookup/reference data."""
    __abstract__ = True

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )