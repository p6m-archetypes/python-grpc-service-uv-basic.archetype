"""Test fixtures and utilities for Example Service testing."""

import asyncio
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

# Note: These imports will work once we set up proper dependencies
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.persistence.database_config import DatabaseConfig, init_database
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.persistence.repositories.example_repository import ExampleRepository
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.core.example_service_core import ExampleServiceCore
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.api.models import ExampleDto


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
@pytest.mark.requires_docker
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container for testing."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.start()
        yield postgres


@pytest.fixture(scope="session")
@pytest.mark.requires_docker
def database_url(postgres_container: PostgresContainer) -> str:
    """Get the database URL for the test PostgreSQL container."""
    return postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")


@pytest_asyncio.fixture(scope="session")
@pytest.mark.requires_docker
async def db_config(database_url: str):
    """Create and initialize database configuration for testing."""
    # This will be implemented once we have the actual database module
    # db_config = DatabaseConfig(database_url, echo=True)
    # await db_config.create_tables()
    # yield db_config
    # await db_config.close()
    
    # Placeholder for now
    db_config = type('DatabaseConfig', (), {
        'get_session': lambda: type('AsyncContextManager', (), {
            '__aenter__': lambda self: type('Session', (), {})(),
            '__aexit__': lambda self, *args: None
        })(),
        'create_tables': lambda: None,
        'close': lambda: None
    })()
    yield db_config


@pytest_asyncio.fixture
@pytest.mark.requires_docker
async def db_session(db_config):
    """Create a database session for testing."""
    async with db_config.get_session() as session:
        yield session


@pytest_asyncio.fixture
@pytest.mark.requires_docker
async def example_repository(db_session):
    """Create an ExampleRepository for testing."""
    # This will be implemented once we have the actual repository
    # return ExampleRepository(db_session)
    
    # Placeholder for now
    return type('ExampleRepository', (), {
        'save': lambda self, data: type('Entity', (), {
            'id': uuid.uuid4(),
            'name': data.get('name', 'test')
        })(),
        'find_by_id': lambda self, id: None,
        'find_all_paginated': lambda self, page, size: type('PageResult', (), {
            'items': [],
            'total_elements': 0,
            'total_pages': 0,
            'has_next': False,
            'has_previous': False,
            'next_page': 0,
            'previous_page': 0
        })(),
        'update': lambda self, id, data: None,
        'delete_by_id': lambda self, id: True,
        'exists_by_id': lambda self, id: False
    })()


@pytest_asyncio.fixture
@pytest.mark.requires_docker
async def example_service_core(example_repository):
    """Create an ExampleServiceCore for testing."""
    # This will be implemented once we have the actual service
    # return ExampleServiceCore(example_repository)
    
    # Placeholder for now
    return type('ExampleServiceCore', (), {
        'create_example': lambda self, example: type('CreateExampleResponse', (), {
            'example': type('ExampleDto', (), {
                'id': str(uuid.uuid4()),
                'name': example.name
            })()
        })(),
        'get_examples': lambda self, request: type('GetExamplesResponse', (), {
            'examples': [],
            'has_next': False,
            'has_previous': False,
            'next_page': 0,
            'previous_page': 0,
            'total_pages': 0,
            'total_elements': 0
        })(),
        'get_example': lambda self, request: type('GetExampleResponse', (), {
            'example': type('ExampleDto', (), {
                'id': request.id,
                'name': 'test-example'
            })()
        })(),
        'update_example': lambda self, example: type('UpdateExampleResponse', (), {
            'example': example
        })(),
        'delete_example': lambda self, request: type('DeleteExampleResponse', (), {
            'message': 'Successfully deleted example'
        })()
    })()


@pytest.fixture
def sample_example_dto():
    """Create a sample ExampleDto for testing."""
    return type('ExampleDto', (), {
        'id': None,
        'name': 'Test Example'
    })()


@pytest.fixture
def sample_example_dto_with_id():
    """Create a sample ExampleDto with ID for testing."""
    return type('ExampleDto', (), {
        'id': str(uuid.uuid4()),
        'name': 'Test Example with ID'
    })()


@pytest.fixture
def sample_get_examples_request():
    """Create a sample GetExamplesRequest for testing."""
    return type('GetExamplesRequest', (), {
        'start_page': 0,
        'page_size': 10
    })()


@pytest.fixture
def sample_get_example_request():
    """Create a sample GetExampleRequest for testing."""
    return type('GetExampleRequest', (), {
        'id': str(uuid.uuid4())
    })()


@pytest.fixture
def sample_delete_example_request():
    """Create a sample DeleteExampleRequest for testing."""
    return type('DeleteExampleRequest', (), {
        'id': str(uuid.uuid4())
    })()


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_example_dto(name: str = "Test Example", example_id: str = None):
        """Create an ExampleDto for testing."""
        return type('ExampleDto', (), {
            'id': example_id,
            'name': name
        })()
    
    @staticmethod
    def create_get_examples_request(start_page: int = 0, page_size: int = 10):
        """Create a GetExamplesRequest for testing."""
        return type('GetExamplesRequest', (), {
            'start_page': start_page,
            'page_size': page_size
        })()
    
    @staticmethod
    def create_get_example_request(example_id: str):
        """Create a GetExampleRequest for testing."""
        return type('GetExampleRequest', (), {
            'id': example_id
        })()
    
    @staticmethod
    def create_delete_example_request(example_id: str):
        """Create a DeleteExampleRequest for testing."""
        return type('DeleteExampleRequest', (), {
            'id': example_id
        })()


@pytest.fixture
def test_data_factory():
    """Provide access to the TestDataFactory."""
    return TestDataFactory