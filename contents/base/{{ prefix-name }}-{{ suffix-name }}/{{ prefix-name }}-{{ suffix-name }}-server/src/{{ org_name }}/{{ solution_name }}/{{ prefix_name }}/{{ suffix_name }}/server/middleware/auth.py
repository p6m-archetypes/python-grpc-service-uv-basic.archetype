"""Authentication and authorization middleware for gRPC services."""

import logging
from typing import Any, Callable, Dict, Optional, Set

import grpc
import jwt
from grpc import StatusCode

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, status_code: StatusCode = StatusCode.UNAUTHENTICATED):
        super().__init__(message)
        self.status_code = status_code


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, status_code: StatusCode = StatusCode.PERMISSION_DENIED):
        super().__init__(message)
        self.status_code = status_code


class JWTAuthenticator:
    """JWT-based authentication handler."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        verify_exp: bool = True,
        verify_aud: bool = False,
        audience: Optional[str] = None
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.verify_exp = verify_exp
        self.verify_aud = verify_aud
        self.audience = audience
    
    def authenticate(self, token: str) -> Dict[str, Any]:
        """Authenticate a JWT token and return the payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded JWT payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            options = {
                "verify_exp": self.verify_exp,
                "verify_aud": self.verify_aud,
            }
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience if self.verify_aud else None,
                options=options
            )
            
            logger.debug(f"Successfully authenticated user: {payload.get('sub', 'unknown')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired", StatusCode.UNAUTHENTICATED)
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}", StatusCode.UNAUTHENTICATED)
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError("Authentication failed", StatusCode.INTERNAL)


class RoleBasedAuthorizer:
    """Role-based authorization handler."""
    
    def __init__(self, method_permissions: Dict[str, Set[str]]):
        """Initialize with method-to-roles mapping.
        
        Args:
            method_permissions: Dict mapping method names to required roles
        """
        self.method_permissions = method_permissions
    
    def authorize(self, method_name: str, user_roles: Set[str]) -> None:
        """Check if user has required permissions for the method.
        
        Args:
            method_name: gRPC method name
            user_roles: Set of user roles
            
        Raises:
            AuthorizationError: If user lacks required permissions
        """
        required_roles = self.method_permissions.get(method_name, set())
        
        if not required_roles:
            # No specific permissions required
            return
        
        if not user_roles.intersection(required_roles):
            logger.warning(
                f"Authorization failed for method {method_name}. "
                f"Required roles: {required_roles}, User roles: {user_roles}"
            )
            raise AuthorizationError(
                f"Insufficient permissions for {method_name}",
                StatusCode.PERMISSION_DENIED
            )
        
        logger.debug(f"Authorization successful for method {method_name}")


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """gRPC server interceptor for authentication and authorization."""
    
    def __init__(
        self,
        authenticator: JWTAuthenticator,
        authorizer: Optional[RoleBasedAuthorizer] = None,
        public_methods: Optional[Set[str]] = None
    ):
        """Initialize auth interceptor.
        
        Args:
            authenticator: JWT authenticator instance
            authorizer: Optional role-based authorizer
            public_methods: Set of method names that don't require auth
        """
        self.authenticator = authenticator
        self.authorizer = authorizer
        self.public_methods = public_methods or {
            "/grpc.health.v1.Health/Check",
            "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo"
        }
    
    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Intercept gRPC service calls for authentication/authorization."""
        method_name = handler_call_details.method
        
        # Skip auth for public methods
        if method_name in self.public_methods:
            return await continuation(handler_call_details)
        
        # Extract authorization header
        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get("authorization")
        
        if not auth_header:
            logger.warning(f"Missing authorization header for method: {method_name}")
            raise grpc.aio.AioRpcError(
                grpc.StatusCode.UNAUTHENTICATED,
                "Missing authorization header"
            )
        
        # Extract Bearer token
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Invalid authorization header format for method: {method_name}")
            raise grpc.aio.AioRpcError(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid authorization header format"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Authenticate token
            payload = self.authenticator.authenticate(token)
            
            # Extract user info
            user_id = payload.get("sub")
            user_roles = set(payload.get("roles", []))
            
            # Store user context in metadata for downstream use
            enhanced_metadata = [
                ("x-user-id", user_id),
                ("x-user-roles", ",".join(user_roles)),
            ]
            enhanced_metadata.extend(handler_call_details.invocation_metadata)
            
            # Create new handler call details with enhanced metadata
            enhanced_handler_call_details = grpc.HandlerCallDetails(
                method=handler_call_details.method,
                invocation_metadata=enhanced_metadata
            )
            
            # Authorize if authorizer is configured
            if self.authorizer:
                self.authorizer.authorize(method_name, user_roles)
            
            logger.info(f"Authenticated request for user {user_id} to method {method_name}")
            return await continuation(enhanced_handler_call_details)
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed for method {method_name}: {e}")
            raise grpc.aio.AioRpcError(e.status_code, str(e))
        except AuthorizationError as e:
            logger.warning(f"Authorization failed for method {method_name}: {e}")
            raise grpc.aio.AioRpcError(e.status_code, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in auth interceptor: {e}")
            raise grpc.aio.AioRpcError(
                grpc.StatusCode.INTERNAL,
                "Internal authentication error"
            )


def create_auth_interceptor(
    secret_key: str,
    method_permissions: Optional[Dict[str, Set[str]]] = None,
    public_methods: Optional[Set[str]] = None,
    **jwt_kwargs
) -> AuthInterceptor:
    """Factory function to create a configured auth interceptor.
    
    Args:
        secret_key: JWT secret key
        method_permissions: Optional method-to-roles mapping
        public_methods: Optional set of public methods
        **jwt_kwargs: Additional JWT configuration options
        
    Returns:
        Configured AuthInterceptor instance
    """
    authenticator = JWTAuthenticator(secret_key, **jwt_kwargs)
    
    authorizer = None
    if method_permissions:
        authorizer = RoleBasedAuthorizer(method_permissions)
    
    return AuthInterceptor(
        authenticator=authenticator,
        authorizer=authorizer,
        public_methods=public_methods
    )