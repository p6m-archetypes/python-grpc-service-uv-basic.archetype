"""Rate limiting middleware for gRPC services."""

import asyncio
import time
from collections import defaultdict
from typing import Any, Callable, Dict

import grpc
import structlog

logger = structlog.get_logger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        async with self._lock:
            now = time.time()
            # Refill tokens based on time elapsed
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.refill_rate)
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimitingInterceptor(grpc.aio.ServerInterceptor):
    """gRPC interceptor for rate limiting requests."""

    def __init__(
        self,
        requests_per_second: int = 100,
        burst_capacity: int = 200,
        cleanup_interval: int = 300  # 5 minutes
    ):
        """Initialize rate limiting interceptor.
        
        Args:
            requests_per_second: Maximum requests per second per client
            burst_capacity: Maximum burst requests allowed
            cleanup_interval: How often to clean up old buckets (seconds)
        """
        self.requests_per_second = requests_per_second
        self.burst_capacity = burst_capacity
        self.cleanup_interval = cleanup_interval
        
        # Store token buckets per client
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        self._lock = asyncio.Lock()

    def _get_client_key(self, handler_call_details: grpc.HandlerCallDetails) -> str:
        """Extract client identifier for rate limiting.
        
        Args:
            handler_call_details: gRPC call details
            
        Returns:
            Client identifier (IP address or authenticated user ID)
        """
        # In a real implementation, you'd extract the client IP or user ID
        # For now, we'll use a simple peer identifier
        metadata = dict(handler_call_details.invocation_metadata)
        
        # Try to get client ID from metadata (e.g., API key, user ID)
        client_id = metadata.get('x-client-id')
        if client_id:
            return f"client:{client_id}"
        
        # Fall back to peer address (in real implementation)
        # peer = handler_call_details.peer or "unknown"
        return "default"  # For demonstration, use a default key

    async def _cleanup_old_buckets(self):
        """Clean up old, unused token buckets."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        async with self._lock:
            # Remove buckets that haven't been used recently
            cutoff_time = now - self.cleanup_interval
            to_remove = []
            
            for key, bucket in self.buckets.items():
                if bucket.last_refill < cutoff_time:
                    to_remove.append(key)
            
            for key in to_remove:
                del self.buckets[key]
                logger.debug("Cleaned up unused rate limit bucket", client_key=key)
            
            self.last_cleanup = now

    async def _get_bucket(self, client_key: str) -> TokenBucket:
        """Get or create a token bucket for a client.
        
        Args:
            client_key: Client identifier
            
        Returns:
            Token bucket for the client
        """
        async with self._lock:
            if client_key not in self.buckets:
                self.buckets[client_key] = TokenBucket(
                    capacity=self.burst_capacity,
                    refill_rate=self.requests_per_second
                )
                logger.debug("Created new rate limit bucket", client_key=client_key)
            
            return self.buckets[client_key]

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """Intercept gRPC calls to apply rate limiting.
        
        Args:
            continuation: The next interceptor or handler
            handler_call_details: Details about the handler call
            
        Returns:
            The result of the service call
            
        Raises:
            grpc.RpcError: If rate limit is exceeded
        """
        # Clean up old buckets periodically
        await self._cleanup_old_buckets()
        
        # Get client identifier
        client_key = self._get_client_key(handler_call_details)
        
        # Get token bucket for this client
        bucket = await self._get_bucket(client_key)
        
        # Try to consume a token
        if await bucket.consume():
            logger.debug(
                "Request allowed by rate limiter",
                client_key=client_key,
                method=handler_call_details.method,
                remaining_tokens=bucket.tokens
            )
            
            # Continue with the request
            return await continuation(handler_call_details)
        else:
            # Rate limit exceeded
            logger.warning(
                "Rate limit exceeded",
                client_key=client_key,
                method=handler_call_details.method,
                requests_per_second=self.requests_per_second
            )
            
            # Return rate limit error
            context = grpc.aio.ServicerContext()
            await context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                "Rate limit exceeded. Please slow down your requests."
            )


class MethodBasedRateLimitingInterceptor(RateLimitingInterceptor):
    """Rate limiting interceptor with per-method limits."""

    def __init__(
        self,
        method_limits: Dict[str, Dict[str, int]] = None,
        default_requests_per_second: int = 100,
        default_burst_capacity: int = 200
    ):
        """Initialize method-based rate limiting interceptor.
        
        Args:
            method_limits: Per-method rate limits
            default_requests_per_second: Default requests per second
            default_burst_capacity: Default burst capacity
        """
        super().__init__(default_requests_per_second, default_burst_capacity)
        
        self.method_limits = method_limits or {
            'CreateExample': {'rps': 10, 'burst': 20},
            'UpdateExample': {'rps': 20, 'burst': 40},
            'DeleteExample': {'rps': 5, 'burst': 10},
            'GetExample': {'rps': 100, 'burst': 200},
            'GetExamples': {'rps': 50, 'burst': 100}
        }

    def _get_method_limits(self, method: str) -> tuple[int, int]:
        """Get rate limits for a specific method.
        
        Args:
            method: gRPC method name
            
        Returns:
            Tuple of (requests_per_second, burst_capacity)
        """
        # Extract method name from full path
        method_name = method.split('/')[-1] if '/' in method else method
        
        if method_name in self.method_limits:
            limits = self.method_limits[method_name]
            return limits['rps'], limits['burst']
        
        return self.requests_per_second, self.burst_capacity

    async def _get_bucket(self, client_key: str, method: str) -> TokenBucket:
        """Get or create a token bucket for a client and method.
        
        Args:
            client_key: Client identifier
            method: gRPC method
            
        Returns:
            Token bucket for the client and method
        """
        # Include method in the bucket key
        bucket_key = f"{client_key}:{method}"
        
        async with self._lock:
            if bucket_key not in self.buckets:
                rps, burst = self._get_method_limits(method)
                self.buckets[bucket_key] = TokenBucket(
                    capacity=burst,
                    refill_rate=rps
                )
                logger.debug(
                    "Created new method-specific rate limit bucket",
                    client_key=client_key,
                    method=method,
                    rps=rps,
                    burst=burst
                )
            
            return self.buckets[bucket_key]

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """Intercept gRPC calls to apply method-based rate limiting."""
        await self._cleanup_old_buckets()
        
        client_key = self._get_client_key(handler_call_details)
        method = handler_call_details.method
        
        # Get method-specific token bucket
        bucket = await self._get_bucket(client_key, method)
        
        if await bucket.consume():
            rps, burst = self._get_method_limits(method)
            logger.debug(
                "Request allowed by method-based rate limiter",
                client_key=client_key,
                method=method,
                remaining_tokens=bucket.tokens,
                method_rps=rps
            )
            
            return await continuation(handler_call_details)
        else:
            rps, burst = self._get_method_limits(method)
            logger.warning(
                "Method-based rate limit exceeded",
                client_key=client_key,
                method=method,
                method_rps=rps
            )
            
            context = grpc.aio.ServicerContext()
            await context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                f"Rate limit exceeded for method {method.split('/')[-1]}. "
                f"Limit: {rps} requests per second."
            )