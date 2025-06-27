"""gRPC service implementation for {{ PrefixName }} {{ SuffixName }}."""

import time
import uuid
import grpc
import structlog

# Import the generated protobuf classes
import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2 as pb2
import {{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc.{{ prefix_name }}_{{ suffix_name }}_pb2_grpc as pb2_grpc

logger = structlog.get_logger(__name__)


class {{ PrefixName }}{{ SuffixName }}ServiceImpl(pb2_grpc.{{ PrefixName }}{{ SuffixName }}Servicer):
    """gRPC service implementation for {{ PrefixName }} {{ SuffixName }}."""

    def __init__(self, core_service=None) -> None:
        """Initialize the gRPC service implementation."""
        self.core_service = core_service
        # In-memory storage for demo purposes
        self.{{ prefix_name }}es = {}
        logger.info("{{ PrefixName }} {{ SuffixName }} gRPC service implementation initialized")

    async def Create{{ PrefixName }}(self, request, context):
        """Create a new project prefix."""
        try:
            logger.info("Creating new project prefix", name=request.{{ prefix_name }}.name)
            
            # Generate ID and timestamps
            {{ prefix_name }}_id = str(uuid.uuid4())
            current_time = int(time.time() * 1000)  # milliseconds
            
            # Create project prefix object
            {{ prefix_name }} = pb2.{{ PrefixName }}(
                id={{ prefix_name }}_id,
                name=request.{{ prefix_name }}.name,
                description=request.{{ prefix_name }}.description,
                created_at=current_time,
                updated_at=current_time
            )
            
            # Store in memory (in a real app, this would go to database)
            self.{{ prefix_name }}es[{{ prefix_name }}_id] = {{ prefix_name }}
            
            response = pb2.Create{{ PrefixName }}Response({{ prefix_name }}={{ prefix_name }})
            
            logger.info("Project prefix created successfully", 
                       id={{ prefix_name }}_id, 
                       name={{ prefix_name }}.name)
            
            return response
            
        except Exception as e:
            logger.error("Failed to create project prefix", error=str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create project prefix: {str(e)}")
            return pb2.Create{{ PrefixName }}Response()

    async def Get{{ PrefixName }}s(self, request, context):
        """Get project prefixes with pagination."""
        try:
            logger.info("Getting project prefixes", 
                       start_page=request.start_page, 
                       page_size=request.page_size)
            
            # Convert to list and apply pagination
            all_prefixes = list(self.{{ prefix_name }}es.values())
            start_index = request.start_page * request.page_size
            end_index = start_index + request.page_size
            paginated_prefixes = all_prefixes[start_index:end_index]
            
            response = pb2.Get{{ PrefixName }}sResponse(
                {{ prefix_name }}s=paginated_prefixes,
                total_count=len(all_prefixes)
            )
            
            logger.info("Retrieved project prefixes", 
                       count=len(paginated_prefixes),
                       total=len(all_prefixes))
            
            return response
            
        except Exception as e:
            logger.error("Failed to get project prefixes", error=str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get project prefixes: {str(e)}")
            return pb2.Get{{ PrefixName }}sResponse()