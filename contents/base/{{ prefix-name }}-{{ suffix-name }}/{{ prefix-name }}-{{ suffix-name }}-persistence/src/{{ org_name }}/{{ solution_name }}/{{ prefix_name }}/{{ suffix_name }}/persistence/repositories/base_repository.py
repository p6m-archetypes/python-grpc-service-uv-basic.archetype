"""Base repository with common CRUD operations."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.pagination import PageResult

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Abstract base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, entity_class: Type[T]) -> None:
        """Initialize the repository.
        
        Args:
            session: Async database session
            entity_class: The entity class this repository manages
        """
        self.session = session
        self.entity_class = entity_class

    async def save(self, entity_data: Dict[str, Any]) -> T:
        """Save a new entity.
        
        Args:
            entity_data: Dictionary containing entity data
            
        Returns:
            The saved entity
        """
        entity = self.entity_class(**entity_data)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def find_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        """Find an entity by its ID.
        
        Args:
            entity_id: The entity ID to search for
            
        Returns:
            The entity if found, None otherwise
        """
        stmt = select(self.entity_class).where(self.entity_class.id == entity_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_id(self, entity_id: uuid.UUID) -> bool:
        """Check if an entity exists by ID.
        
        Args:
            entity_id: The entity ID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        stmt = select(func.count()).select_from(
            select(self.entity_class).where(self.entity_class.id == entity_id)
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def find_all_paginated(self, page: int = 0, size: int = 10) -> PageResult[T]:
        """Find all entities with pagination.
        
        Args:
            page: Page number (0-based)
            size: Page size
            
        Returns:
            Paginated results
        """
        # Get total count
        count_stmt = select(func.count()).select_from(self.entity_class)
        count_result = await self.session.execute(count_stmt)
        total_elements = count_result.scalar()

        # Get paginated items
        offset = page * size
        stmt = select(self.entity_class).offset(offset).limit(size)
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        return PageResult.create(
            items=list(items),
            total_elements=total_elements,
            page=page,
            size=size
        )

    async def update(self, entity_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[T]:
        """Update an entity by ID.
        
        Args:
            entity_id: The entity ID to update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated entity if found, None otherwise
        """
        entity = await self.find_by_id(entity_id)
        if not entity:
            return None

        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete_by_id(self, entity_id: uuid.UUID) -> bool:
        """Delete an entity by ID.
        
        Args:
            entity_id: The entity ID to delete
            
        Returns:
            True if entity was deleted, False if not found
        """
        entity = await self.find_by_id(entity_id)
        if not entity:
            return False

        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def find_all(self) -> List[T]:
        """Find all entities (use with caution on large datasets).
        
        Returns:
            List of all entities
        """
        stmt = select(self.entity_class)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total number of entities.
        
        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.entity_class)
        result = await self.session.execute(stmt)
        return result.scalar()

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[T]:
        """Find an entity by name.
        
        Args:
            name: The name to search for
            
        Returns:
            The entity if found, None otherwise
        """
        pass