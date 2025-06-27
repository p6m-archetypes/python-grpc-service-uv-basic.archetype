"""Repository for {{ PrefixName }} entity operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..entities.{{ prefix_name }}_entity import {{ PrefixName }}Entity
from .base_repository import BaseRepository


class {{ PrefixName }}Repository(BaseRepository[{{ PrefixName }}Entity]):
    """Repository for {{ PrefixName }} entity CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the {{ PrefixName }} repository.
        
        Args:
            session: Async database session
        """
        super().__init__(session, {{ PrefixName }}Entity)

    async def find_by_name(self, name: str) -> Optional[{{ PrefixName }}Entity]:
        """Find a project prefix by name.
        
        Args:
            name: The name to search for
            
        Returns:
            The project prefix if found, None otherwise
        """
        stmt = select({{ PrefixName }}Entity).where({{ PrefixName }}Entity.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_containing(self, name_pattern: str) -> List[{{ PrefixName }}Entity]:
        """Find project prefixes where name contains the given pattern.
        
        Args:
            name_pattern: Pattern to search for in names
            
        Returns:
            List of matching project prefixes
        """
        stmt = select({{ PrefixName }}Entity).where(
            {{ PrefixName }}Entity.name.ilike(f"%{name_pattern}%")
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_status(self, status: str) -> List[{{ PrefixName }}Entity]:
        """Find project prefixes by status.
        
        Args:
            status: Status to search for
            
        Returns:
            List of matching project prefixes
        """
        stmt = select({{ PrefixName }}Entity).where(
            {{ PrefixName }}Entity.status == status
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_name(self, name: str) -> bool:
        """Check if a project prefix with the given name exists.
        
        Args:
            name: The name to check
            
        Returns:
            True if a project prefix with this name exists, False otherwise
        """
        stmt = select({{ PrefixName }}Entity).where({{ PrefixName }}Entity.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None