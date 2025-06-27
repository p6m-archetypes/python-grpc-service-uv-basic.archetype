"""gRPC client for Example Service."""

from typing import Optional

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

logger = structlog.get_logger(__name__)


class ExampleServiceClient:
    """Client for connecting to the Example Service gRPC API."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9010,
        channel: Optional[grpc.Channel] = None,
        timeout: float = 30.0
    ) -> None:
        """Initialize the Example Service client.
        
        Args:
            host: gRPC server host
            port: gRPC server port
            channel: Optional existing gRPC channel to use
            timeout: Default timeout for requests in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        
        if channel:
            self.channel = channel
        else:
            # Create an insecure channel (for development)
            # In production, you would typically use secure channels with TLS
            self.channel = grpc.insecure_channel(f"{host}:{port}")
        
        # Create the stub (will be implemented once we have protobuf classes)
        # self.stub = pb2_grpc.ExampleServiceStub(self.channel)
        self.stub = None
        
        logger.info(
            "Example Service client initialized",
            host=host,
            port=port,
            timeout=timeout
        )

    @classmethod
    def create(cls, host: str, port: int) -> "ExampleServiceClient":
        """Factory method to create a client instance.
        
        Args:
            host: gRPC server host
            port: gRPC server port
            
        Returns:
            Configured client instance
        """
        return cls(host=host, port=port)

    async def create_example(self, example: "ExampleDto") -> "CreateExampleResponse":
        """Create a new example.
        
        Args:
            example: Example data to create
            
        Returns:
            Response containing the created example
            
        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        logger.info("Creating example", name=example.name if hasattr(example, 'name') else 'unknown')
        
        try:
            # Convert domain model to protobuf
            pb_request = self._example_dto_to_pb(example)
            
            # Make gRPC call
            # pb_response = await self.stub.CreateExample(pb_request, timeout=self.timeout)
            pb_response = None  # Placeholder
            
            # Convert protobuf response to domain model
            response = self._pb_to_create_example_response(pb_response)
            
            logger.info("Example created successfully", example_id=response.example.id if response.example else None)
            return response
            
        except grpc.RpcError as e:
            logger.error("Failed to create example", error=str(e), grpc_code=e.code())
            raise
        except Exception as e:
            logger.error("Unexpected error creating example", error=str(e), exc_info=True)
            raise

    async def get_examples(self, request: "GetExamplesRequest") -> "GetExamplesResponse":
        """Get a paginated list of examples.
        
        Args:
            request: Pagination request parameters
            
        Returns:
            Response containing examples and pagination metadata
            
        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        logger.info("Getting examples", start_page=request.start_page, page_size=request.page_size)
        
        try:
            # Convert domain model to protobuf
            pb_request = self._get_examples_request_to_pb(request)
            
            # Make gRPC call
            # pb_response = await self.stub.GetExamples(pb_request, timeout=self.timeout)
            pb_response = None  # Placeholder
            
            # Convert protobuf response to domain model
            response = self._pb_to_get_examples_response(pb_response)
            
            logger.info("Examples retrieved successfully", count=len(response.examples))
            return response
            
        except grpc.RpcError as e:
            logger.error("Failed to get examples", error=str(e), grpc_code=e.code())
            raise
        except Exception as e:
            logger.error("Unexpected error getting examples", error=str(e), exc_info=True)
            raise

    async def get_example(self, request: "GetExampleRequest") -> "GetExampleResponse":
        """Get a single example by ID.
        
        Args:
            request: Request containing the example ID
            
        Returns:
            Response containing the requested example
            
        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        logger.info("Getting example", example_id=request.id)
        
        try:
            # Convert domain model to protobuf
            pb_request = self._get_example_request_to_pb(request)
            
            # Make gRPC call
            # pb_response = await self.stub.GetExample(pb_request, timeout=self.timeout)
            pb_response = None  # Placeholder
            
            # Convert protobuf response to domain model
            response = self._pb_to_get_example_response(pb_response)
            
            logger.info("Example retrieved successfully", example_id=response.example.id if response.example else None)
            return response
            
        except grpc.RpcError as e:
            logger.error("Failed to get example", error=str(e), grpc_code=e.code())
            raise
        except Exception as e:
            logger.error("Unexpected error getting example", error=str(e), exc_info=True)
            raise

    async def update_example(self, example: "ExampleDto") -> "UpdateExampleResponse":
        """Update an existing example.
        
        Args:
            example: Updated example data
            
        Returns:
            Response containing the updated example
            
        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        logger.info("Updating example", example_id=example.id if hasattr(example, 'id') else 'unknown')
        
        try:
            # Convert domain model to protobuf
            pb_request = self._example_dto_to_pb(example)
            
            # Make gRPC call
            # pb_response = await self.stub.UpdateExample(pb_request, timeout=self.timeout)
            pb_response = None  # Placeholder
            
            # Convert protobuf response to domain model
            response = self._pb_to_update_example_response(pb_response)
            
            logger.info("Example updated successfully", example_id=response.example.id if response.example else None)
            return response
            
        except grpc.RpcError as e:
            logger.error("Failed to update example", error=str(e), grpc_code=e.code())
            raise
        except Exception as e:
            logger.error("Unexpected error updating example", error=str(e), exc_info=True)
            raise

    async def delete_example(self, request: "DeleteExampleRequest") -> "DeleteExampleResponse":
        """Delete an example by ID.
        
        Args:
            request: Request containing the example ID to delete
            
        Returns:
            Response with confirmation message
            
        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        logger.info("Deleting example", example_id=request.id)
        
        try:
            # Convert domain model to protobuf
            pb_request = self._delete_example_request_to_pb(request)
            
            # Make gRPC call
            # pb_response = await self.stub.DeleteExample(pb_request, timeout=self.timeout)
            pb_response = None  # Placeholder
            
            # Convert protobuf response to domain model
            response = self._pb_to_delete_example_response(pb_response)
            
            logger.info("Example deleted successfully", message=response.message)
            return response
            
        except grpc.RpcError as e:
            logger.error("Failed to delete example", error=str(e), grpc_code=e.code())
            raise
        except Exception as e:
            logger.error("Unexpected error deleting example", error=str(e), exc_info=True)
            raise

    def close(self) -> None:
        """Close the gRPC channel."""
        if self.channel:
            self.channel.close()
            logger.info("gRPC channel closed")

    def __enter__(self) -> "ExampleServiceClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    # Conversion methods (placeholders until we have actual protobuf classes)
    
    def _example_dto_to_pb(self, example_dto):
        """Convert domain ExampleDto to protobuf ExampleDto."""
        # Placeholder implementation
        return type('ExampleDto', (), {
            'id': type('StringValue', (), {'value': example_dto.id})() if example_dto.id else None,
            'name': example_dto.name
        })()

    def _get_examples_request_to_pb(self, request):
        """Convert domain GetExamplesRequest to protobuf."""
        return type('GetExamplesRequest', (), {
            'start_page': request.start_page,
            'page_size': request.page_size
        })()

    def _get_example_request_to_pb(self, request):
        """Convert domain GetExampleRequest to protobuf."""
        return type('GetExampleRequest', (), {
            'id': request.id
        })()

    def _delete_example_request_to_pb(self, request):
        """Convert domain DeleteExampleRequest to protobuf."""
        return type('DeleteExampleRequest', (), {
            'id': request.id
        })()

    def _pb_to_create_example_response(self, pb_response):
        """Convert protobuf CreateExampleResponse to domain model."""
        # Placeholder implementation
        return type('CreateExampleResponse', (), {
            'example': self._pb_to_example_dto(pb_response.example) if pb_response else None
        })()

    def _pb_to_get_examples_response(self, pb_response):
        """Convert protobuf GetExamplesResponse to domain model."""
        # Placeholder implementation
        return type('GetExamplesResponse', (), {
            'examples': [self._pb_to_example_dto(ex) for ex in pb_response.example] if pb_response else [],
            'has_next': pb_response.has_next if pb_response else False,
            'has_previous': pb_response.has_previous if pb_response else False,
            'next_page': pb_response.next_page if pb_response else 0,
            'previous_page': pb_response.previous_page if pb_response else 0,
            'total_pages': pb_response.total_pages if pb_response else 0,
            'total_elements': pb_response.total_elements if pb_response else 0
        })()

    def _pb_to_get_example_response(self, pb_response):
        """Convert protobuf GetExampleResponse to domain model."""
        return type('GetExampleResponse', (), {
            'example': self._pb_to_example_dto(pb_response.example) if pb_response else None
        })()

    def _pb_to_update_example_response(self, pb_response):
        """Convert protobuf UpdateExampleResponse to domain model."""
        return type('UpdateExampleResponse', (), {
            'example': self._pb_to_example_dto(pb_response.example) if pb_response else None
        })()

    def _pb_to_delete_example_response(self, pb_response):
        """Convert protobuf DeleteExampleResponse to domain model."""
        return type('DeleteExampleResponse', (), {
            'message': pb_response.message if pb_response else ''
        })()

    def _pb_to_example_dto(self, pb_example):
        """Convert protobuf ExampleDto to domain ExampleDto."""
        if not pb_example:
            return None
        
        return type('ExampleDto', (), {
            'id': pb_example.id.value if hasattr(pb_example, 'id') and pb_example.id else None,
            'name': pb_example.name if hasattr(pb_example, 'name') else ''
        })()