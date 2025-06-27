"""gRPC service implementation for Example Service."""

import grpc
import structlog

# Note: These imports will work once we set up proper proto generation and dependencies
# import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2 as pb2
# import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2_grpc as pb2_grpc
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.api.models import (
#     CreateExampleResponse,
#     DeleteExampleRequest,
#     DeleteExampleResponse,
#     ExampleDto,
#     GetExampleRequest,
#     GetExampleResponse,
#     GetExamplesRequest,
#     GetExamplesResponse,
#     UpdateExampleResponse,
# )
# from {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.core.example_service_core import ExampleServiceCore

from ..exception.grpc_error_mapper import grpc_exception_handler

logger = structlog.get_logger(__name__)


class ExampleServiceGrpcImpl:
    """gRPC service implementation for Example Service."""

    def __init__(self, example_service_core) -> None:
        """Initialize the gRPC service implementation.
        
        Args:
            example_service_core: Core business logic service
        """
        self.example_service_core = example_service_core

    @grpc_exception_handler
    async def CreateExample(self, request, context):
        """Create a new example.
        
        Args:
            request: CreateExample gRPC request
            context: gRPC service context
            
        Returns:
            CreateExampleResponse
        """
        correlation_id = self._get_correlation_id(context)
        logger.info(
            "gRPC CreateExample request received",
            correlation_id=correlation_id,
            has_id=bool(request.id),
            name_length=len(request.name) if request.name else 0
        )

        # Convert gRPC request to domain model
        example_dto = self._pb_to_example_dto(request)
        
        # Call business logic
        response = await self.example_service_core.create_example(example_dto)
        
        # Convert domain response to gRPC response
        grpc_response = self._create_example_response_to_pb(response)
        
        logger.info(
            "gRPC CreateExample request completed",
            correlation_id=correlation_id,
            created_id=response.example.id if response.example else None
        )
        
        return grpc_response

    @grpc_exception_handler
    async def GetExamples(self, request, context):
        """Get a paginated list of examples.
        
        Args:
            request: GetExamples gRPC request
            context: gRPC service context
            
        Returns:
            GetExamplesResponse
        """
        correlation_id = self._get_correlation_id(context)
        logger.info(
            "gRPC GetExamples request received",
            correlation_id=correlation_id,
            start_page=request.start_page,
            page_size=request.page_size
        )

        # Convert gRPC request to domain model
        get_examples_request = self._pb_to_get_examples_request(request)
        
        # Call business logic
        response = await self.example_service_core.get_examples(get_examples_request)
        
        # Convert domain response to gRPC response
        grpc_response = self._get_examples_response_to_pb(response)
        
        logger.info(
            "gRPC GetExamples request completed",
            correlation_id=correlation_id,
            examples_count=len(response.examples),
            total_elements=response.total_elements
        )
        
        return grpc_response

    @grpc_exception_handler
    async def GetExample(self, request, context):
        """Get a single example by ID.
        
        Args:
            request: GetExample gRPC request
            context: gRPC service context
            
        Returns:
            GetExampleResponse
        """
        correlation_id = self._get_correlation_id(context)
        logger.info(
            "gRPC GetExample request received",
            correlation_id=correlation_id,
            example_id=request.id
        )

        # Convert gRPC request to domain model
        get_example_request = self._pb_to_get_example_request(request)
        
        # Call business logic
        response = await self.example_service_core.get_example(get_example_request)
        
        # Convert domain response to gRPC response
        grpc_response = self._get_example_response_to_pb(response)
        
        logger.info(
            "gRPC GetExample request completed",
            correlation_id=correlation_id,
            example_id=response.example.id if response.example else None
        )
        
        return grpc_response

    @grpc_exception_handler
    async def UpdateExample(self, request, context):
        """Update an existing example.
        
        Args:
            request: UpdateExample gRPC request
            context: gRPC service context
            
        Returns:
            UpdateExampleResponse
        """
        correlation_id = self._get_correlation_id(context)
        logger.info(
            "gRPC UpdateExample request received",
            correlation_id=correlation_id,
            example_id=request.id.value if request.HasField('id') else None,
            name=request.name
        )

        # Convert gRPC request to domain model
        example_dto = self._pb_to_example_dto(request)
        
        # Call business logic
        response = await self.example_service_core.update_example(example_dto)
        
        # Convert domain response to gRPC response
        grpc_response = self._update_example_response_to_pb(response)
        
        logger.info(
            "gRPC UpdateExample request completed",
            correlation_id=correlation_id,
            updated_id=response.example.id if response.example else None
        )
        
        return grpc_response

    @grpc_exception_handler
    async def DeleteExample(self, request, context):
        """Delete an example by ID.
        
        Args:
            request: DeleteExample gRPC request
            context: gRPC service context
            
        Returns:
            DeleteExampleResponse
        """
        correlation_id = self._get_correlation_id(context)
        logger.info(
            "gRPC DeleteExample request received",
            correlation_id=correlation_id,
            example_id=request.id
        )

        # Convert gRPC request to domain model
        delete_example_request = self._pb_to_delete_example_request(request)
        
        # Call business logic
        response = await self.example_service_core.delete_example(delete_example_request)
        
        # Convert domain response to gRPC response
        grpc_response = self._delete_example_response_to_pb(response)
        
        logger.info(
            "gRPC DeleteExample request completed",
            correlation_id=correlation_id,
            message=response.message
        )
        
        return grpc_response

    def _get_correlation_id(self, context) -> str:
        """Extract correlation ID from gRPC context.
        
        Args:
            context: gRPC service context
            
        Returns:
            Correlation ID or generated UUID
        """
        # Look for correlation ID in metadata
        metadata = dict(context.invocation_metadata())
        correlation_id = metadata.get('x-correlation-id')
        
        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())
        
        return correlation_id

    def _pb_to_example_dto(self, pb_request):
        """Convert protobuf ExampleDto to domain ExampleDto.
        
        Args:
            pb_request: Protobuf request
            
        Returns:
            Domain ExampleDto
        """
        # This will be implemented once we have the actual protobuf classes
        # For now, return a placeholder
        return type('ExampleDto', (), {
            'id': pb_request.id.value if hasattr(pb_request, 'id') and pb_request.HasField('id') else None,
            'name': pb_request.name if hasattr(pb_request, 'name') else ''
        })()

    def _pb_to_get_examples_request(self, pb_request):
        """Convert protobuf GetExamplesRequest to domain GetExamplesRequest.
        
        Args:
            pb_request: Protobuf request
            
        Returns:
            Domain GetExamplesRequest
        """
        return type('GetExamplesRequest', (), {
            'start_page': pb_request.start_page,
            'page_size': pb_request.page_size
        })()

    def _pb_to_get_example_request(self, pb_request):
        """Convert protobuf GetExampleRequest to domain GetExampleRequest.
        
        Args:
            pb_request: Protobuf request
            
        Returns:
            Domain GetExampleRequest
        """
        return type('GetExampleRequest', (), {
            'id': pb_request.id
        })()

    def _pb_to_delete_example_request(self, pb_request):
        """Convert protobuf DeleteExampleRequest to domain DeleteExampleRequest.
        
        Args:
            pb_request: Protobuf request
            
        Returns:
            Domain DeleteExampleRequest
        """
        return type('DeleteExampleRequest', (), {
            'id': pb_request.id
        })()

    def _create_example_response_to_pb(self, domain_response):
        """Convert domain CreateExampleResponse to protobuf.
        
        Args:
            domain_response: Domain response
            
        Returns:
            Protobuf response
        """
        # Placeholder implementation
        return type('CreateExampleResponse', (), {
            'example': self._example_dto_to_pb(domain_response.example)
        })()

    def _get_examples_response_to_pb(self, domain_response):
        """Convert domain GetExamplesResponse to protobuf.
        
        Args:
            domain_response: Domain response
            
        Returns:
            Protobuf response
        """
        # Placeholder implementation
        return type('GetExamplesResponse', (), {
            'example': [self._example_dto_to_pb(ex) for ex in domain_response.examples],
            'has_next': domain_response.has_next,
            'has_previous': domain_response.has_previous,
            'next_page': domain_response.next_page,
            'previous_page': domain_response.previous_page,
            'total_pages': domain_response.total_pages,
            'total_elements': domain_response.total_elements
        })()

    def _get_example_response_to_pb(self, domain_response):
        """Convert domain GetExampleResponse to protobuf.
        
        Args:
            domain_response: Domain response
            
        Returns:
            Protobuf response
        """
        # Placeholder implementation
        return type('GetExampleResponse', (), {
            'example': self._example_dto_to_pb(domain_response.example)
        })()

    def _update_example_response_to_pb(self, domain_response):
        """Convert domain UpdateExampleResponse to protobuf.
        
        Args:
            domain_response: Domain response
            
        Returns:
            Protobuf response
        """
        # Placeholder implementation
        return type('UpdateExampleResponse', (), {
            'example': self._example_dto_to_pb(domain_response.example)
        })()

    def _delete_example_response_to_pb(self, domain_response):
        """Convert domain DeleteExampleResponse to protobuf.
        
        Args:
            domain_response: Domain response
            
        Returns:
            Protobuf response
        """
        # Placeholder implementation
        return type('DeleteExampleResponse', (), {
            'message': domain_response.message
        })()

    def _example_dto_to_pb(self, example_dto):
        """Convert domain ExampleDto to protobuf ExampleDto.
        
        Args:
            example_dto: Domain ExampleDto
            
        Returns:
            Protobuf ExampleDto
        """
        # Placeholder implementation
        return type('ExampleDto', (), {
            'id': type('StringValue', (), {'value': example_dto.id})(),
            'name': example_dto.name
        })()