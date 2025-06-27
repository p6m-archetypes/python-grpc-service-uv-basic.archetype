"""{{ PrefixName }} entity definition."""

import uuid
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models.base import AbstractCreatedModifiedVersioned


class {{ PrefixName }}Entity(AbstractCreatedModifiedVersioned):
    """Entity representing a {{ PrefixName }} record."""
    
    __tablename__ = "{{ prefix_name }}"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the project prefix"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the project prefix"
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
        comment="Status of the project prefix"
    )

    def __init__(self, name: str, description: Optional[str] = None, status: str = "ACTIVE", id: Optional[uuid.UUID] = None) -> None:
        """Initialize a {{ PrefixName }}Entity.
        
        Args:
            name: The name of the project prefix
            description: Optional description
            status: Status (defaults to ACTIVE)
            id: Optional UUID, will be generated if not provided
        """
        if id is not None:
            self.id = id
        self.name = name
        self.description = description
        self.status = status

    def __repr__(self) -> str:
        """String representation of the entity."""
        return f"{{ PrefixName }}Entity(id='{self.id}', name='{self.name}', status='{self.status}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{{ PrefixName }} {self.id}: {self.name} ({self.status})"