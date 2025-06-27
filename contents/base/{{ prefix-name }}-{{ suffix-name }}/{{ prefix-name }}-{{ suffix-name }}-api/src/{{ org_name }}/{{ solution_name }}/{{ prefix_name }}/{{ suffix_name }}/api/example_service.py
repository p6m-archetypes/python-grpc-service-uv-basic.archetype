"""{{ SuffixName }} interface definition for the {{ PrefixName }} {{ SuffixName }}."""

from abc import ABC, abstractmethod

from .models import (
    Create{{ PrefixName }}Response,
    Delete{{ PrefixName }}Request,
    Delete{{ PrefixName }}Response,
    {{ PrefixName }}Dto,
    Get{{ PrefixName }}Request,
    Get{{ PrefixName }}Response,
    Get{{ PrefixName }}sRequest,
    Get{{ PrefixName }}sResponse,
    Update{{ PrefixName }}Response,
)


class {{ PrefixName }}{{ SuffixName }}(ABC):
    """Abstract interface for the {{ PrefixName }} {{ SuffixName }} business logic."""

    @abstractmethod
    async def create_{{ prefix_name }}(self, {{ prefix_name }}: {{ PrefixName }}Dto) -> Create{{ PrefixName }}Response:
        """Create a new {{ prefix-name }}.
        
        Args:
            {{ prefix_name }}: The {{ prefix-name }} data to create
            
        Returns:
            Response containing the created {{ prefix-name }}
            
        Raises:
            ServiceException: If creation fails
        """
        pass

    @abstractmethod
    async def get_{{ prefix_name }}s(self, request: Get{{ PrefixName }}sRequest) -> Get{{ PrefixName }}sResponse:
        """Get a paginated list of {{ prefix-name }}s.
        
        Args:
            request: Pagination request parameters
            
        Returns:
            Response containing {{ prefix-name }}s and pagination metadata
            
        Raises:
            ServiceException: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_{{ prefix_name }}(self, request: Get{{ PrefixName }}Request) -> Get{{ PrefixName }}Response:
        """Get a single {{ prefix-name }} by ID.
        
        Args:
            request: Request containing the {{ prefix-name }} ID
            
        Returns:
            Response containing the requested {{ prefix-name }}
            
        Raises:
            ServiceException: If {{ prefix-name }} not found or retrieval fails
        """
        pass

    @abstractmethod
    async def update_{{ prefix_name }}(self, {{ prefix_name }}: {{ PrefixName }}Dto) -> Update{{ PrefixName }}Response:
        """Update an existing {{ prefix-name }}.
        
        Args:
            {{ prefix_name }}: The updated {{ prefix-name }} data
            
        Returns:
            Response containing the updated {{ prefix-name }}
            
        Raises:
            ServiceException: If {{ prefix-name }} not found or update fails
        """
        pass

    @abstractmethod
    async def delete_{{ prefix_name }}(self, request: Delete{{ PrefixName }}Request) -> Delete{{ PrefixName }}Response:
        """Delete a {{ prefix-name }} by ID.
        
        Args:
            request: Request containing the {{ prefix-name }} ID to delete
            
        Returns:
            Response with confirmation message
            
        Raises:
            ServiceException: If {{ prefix-name }} not found or deletion fails
        """
        pass