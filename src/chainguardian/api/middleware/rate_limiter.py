"""
Rate limiting middleware for ChainGuardian API.

This module implements token bucket rate limiting using Redis as a distributed counter.
Rate limits are applied per client IP address and per endpoint to prevent API abuse
and ensure fair resource allocation across users.

Key Features:
- Redis-backed distributed rate limiting (works across multiple API instances)
- Configurable limits per endpoint
- Automatic exemption for private/internal network traffic
- Standard HTTP 429 responses with Retry-After headers
- Prometheus metrics integration for monitoring
"""
from typing import Optional, Dict, Callable, Awaitable, cast
import redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, field_validator
import time
import ipaddress

from chainguardian.monitoring.llm_metrics import rate_limit_exceeded_total


class RateLimitConfig(BaseModel):
    """
    Configuration for rate limiting on a specific endpoint.

    Attributes:
        limit: Maximum number of requests allowed within the time window
        window: Time window in seconds for the rate limit (sliding window)

    Example:
        >>> config = RateLimitConfig(limit=10, window=60)  # 10 requests per minute
        >>> config.limit
        10
        >>> config.window
        60
    """
    limit: int = Field(gt=0, description="Maximum requests allowed in the time window")
    window: int = Field(gt=0, description="Time window in seconds")

    @field_validator('limit', 'window')
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Ensure limit and window are positive integers."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that enforces rate limits on API endpoints using Redis.

    This middleware intercepts all incoming HTTP requests and checks if the client
    has exceeded their allowed request quota for the specific endpoint. Rate limits
    are tracked using Redis keys with automatic expiration.

    Algorithm:
        1. Extract client IP from request
        2. Skip rate limiting for private/internal IPs (Docker networks, localhost)
        3. Match request path to configured rate limits
        4. Check Redis for current request count
        5. If limit exceeded, return 429 Too Many Requests
        6. Otherwise, increment counter and pass request through

    Attributes:
        redis_client: Redis client for distributed counter storage
        limits: Dictionary mapping endpoint paths to their rate limit configurations
    """

    def __init__(
        self,
        app: FastAPI,
        redis_url: str,
        limits: Optional[Dict[str, Dict[str, int]]] = None
    ) -> None:
        """
        Initialize the rate limiting middleware.

        Args:
            app: FastAPI application instance
            redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0')
            limits: Optional dictionary of endpoint rate limits. Keys are URL paths,
                   values are dicts with 'limit' (max requests) and 'window' (seconds).
                   Defaults to predefined limits for ChainGuardian endpoints.

        Example:
            >>> middleware = RateLimitMiddleware(
            ...     app=app,
            ...     redis_url="redis://localhost:6379",
            ...     limits={"/api/v1/analyze": {"limit": 10, "window": 60}}
            ... )
        """
        super().__init__(app)
        self.redis_client: redis.Redis = redis.from_url(redis_url)

        # Default rate limits for ChainGuardian API endpoints
        # These can be overridden by passing custom limits
        self.limits: Dict[str, Dict[str, int]] = limits or {
            "/api/v1/analyze": {"limit": 10, "window": 60},  # 10 requests per minute
            "/api/v1/predict-from-features": {"limit": 20, "window": 60},  # 20 per minute
            "/api/v1/reports/generate": {"limit": 5, "window": 60},  # 5 per minute (resource-intensive)
            "/health": {"limit": 30, "window": 60},  # Health checks - higher limit
            "/metrics": {"limit": 30, "window": 60},  # Metrics scraping - higher limit
        }
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process incoming request and enforce rate limits.

        This method is called for every HTTP request. It implements a token bucket
        algorithm using Redis as the backend store for request counts.

        Args:
            request: Incoming HTTP request
            call_next: Callable to pass the request to the next middleware/handler

        Returns:
            HTTP response (either 429 if rate limited, or the actual response)

        Rate Limit Algorithm:
            - Each client+endpoint combination gets a unique Redis key
            - On first request: SET key=1 with TTL=window_seconds
            - On subsequent requests: INCR key (preserves TTL)
            - When TTL expires, Redis auto-deletes the key (counter resets)
        """
        # Extract client IP address from the request
        # Falls back to "unknown" if client info is unavailable (shouldn't happen in practice)
        client_host: str = request.client.host if request.client else "unknown"

        # Optimization: Skip rate limiting for internal/private network traffic
        # This prevents rate limiting between Docker containers or localhost services
        try:
            ip = ipaddress.ip_address(client_host)
            # RFC 1918 private IPs (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            # and loopback (127.0.0.0/8) are exempt from rate limiting
            if ip.is_private or ip.is_loopback:
                response = await call_next(request)
                return response
        except ValueError:
            # If IP parsing fails (e.g., hostname instead of IP), continue with rate limiting
            pass

        # Match the request path to configured rate limits
        path: str = request.url.path
        limit_config: Optional[Dict[str, int]] = None

        # Find the first matching rate limit configuration
        # Uses startswith() to match path prefixes (e.g., "/api/v1/analyze/123" matches "/api/v1/analyze")
        for route, config in self.limits.items():
            if path.startswith(route):
                limit_config = config
                break

        # If this endpoint has rate limiting configured, enforce it
        if limit_config:
            limit: int = limit_config["limit"]  # Max requests allowed
            window: int = limit_config["window"]  # Time window in seconds

            # Create a unique Redis key for this client + endpoint combination
            # Format: "rate_limit:<ip>:<path>"
            # Example: "rate_limit:192.168.1.100:/api/v1/analyze"
            key: str = f"rate_limit:{client_host}:{path}"

            # Get current request count from Redis
            current = self.redis_client.get(key)
            current_count: int = int(cast(bytes, current)) if current else 0

            # Check if rate limit has been exceeded
            if current_count >= limit:
                # Track rate limit violations in Prometheus for monitoring
                rate_limit_exceeded_total.labels(
                    endpoint=path,
                    ip_address=client_host
                ).inc()

                # Get time remaining until the rate limit window resets
                # TTL (Time To Live) returns seconds until key expiration
                ttl_value = cast(int, self.redis_client.ttl(key))
                if ttl_value < 0:  # Key doesn't exist or has no expiry (shouldn't happen)
                    ttl_value = window

                # Return HTTP 429 Too Many Requests with standard headers
                # Following RFC 6585 and best practices for rate limit APIs
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Limit is {limit} per {window} seconds.",
                        "retry_after": ttl_value,
                        "limits": self.limits  # Help clients understand all limits
                    },
                    headers={
                        "Retry-After": str(ttl_value),  # Standard header for rate limiting
                        "X-RateLimit-Limit": str(limit),  # Total quota
                        "X-RateLimit-Remaining": "0",  # No requests left
                        "X-RateLimit-Reset": str(int(time.time() + ttl_value))  # Unix timestamp of reset
                    }
                )

            # Rate limit not exceeded - increment the counter
            if current_count == 0:
                # First request in this window: initialize counter with expiration
                # SETEX atomically sets value and TTL
                self.redis_client.setex(key, window, 1)
            else:
                # Subsequent request: increment existing counter
                # INCR preserves the existing TTL
                self.redis_client.incr(key)

            # Calculate remaining quota for response headers
            remaining: int = limit - (current_count + 1)
            reset_ttl = cast(int, self.redis_client.ttl(key))

            # Process the request through the rest of the middleware chain
            response = await call_next(request)

            # Add rate limit information to the response headers
            # This helps clients implement proper backoff strategies
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))  # Never negative
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + reset_ttl))

            return response

        # No rate limit configured for this endpoint - pass through unchanged
        return await call_next(request)


def setup_rate_limiting(app: FastAPI, redis_url: str, limits: Optional[Dict[str, Dict[str, int]]] = None) -> None:
    """
    Register rate limiting middleware with the FastAPI application.

    This function adds the RateLimitMiddleware to the application's middleware stack.
    The middleware will be applied to all incoming requests before they reach the route handlers.

    Args:
        app: FastAPI application instance to add middleware to
        redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0')
        limits: Optional custom rate limit configurations per endpoint.
               If not provided, uses default ChainGuardian limits.

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> setup_rate_limiting(app, redis_url="redis://localhost:6379")
        >>> # Now all requests will be rate limited according to the default configuration

    Example with custom limits:
        >>> custom_limits = {
        ...     "/api/v1/heavy-operation": {"limit": 5, "window": 60},
        ...     "/api/v1/light-operation": {"limit": 100, "window": 60},
        ... }
        >>> setup_rate_limiting(app, redis_url="redis://localhost:6379", limits=custom_limits)

    Note:
        The middleware is added using add_middleware(), which means it will be applied
        in reverse order of addition (last added = first executed).
    """
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url, limits=limits)  # type: ignore[arg-type]