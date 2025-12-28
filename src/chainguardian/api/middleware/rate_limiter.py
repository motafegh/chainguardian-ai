"""
Rate limiting middleware for ChainGuardian API.
"""
from typing import Optional
import redis
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import ipaddress

from chainguardian.monitoring.llm_metrics import rate_limit_exceeded_total


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(
        self,
        app: FastAPI,
        redis_url: str,
        limits: Optional[dict] = None
    ):
        super().__init__(app)
        self.redis_client = redis.from_url(redis_url)
        self.limits = limits or {
            "/api/v1/analyze": {"limit": 10, "window": 60},  # 10 per minute
            "/api/v1/predict-from-features": {"limit": 20, "window": 60},
            "/api/v1/reports/generate": {"limit": 5, "window": 60},  # 5 per minute
            "/health": {"limit": 30, "window": 60},
            "/metrics": {"limit": 30, "window": 60},
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for internal network requests
        client_host = request.client.host if request.client else "unknown"
        
        # Check if IP is in Docker network (skip for internal)
        try:
            ip = ipaddress.ip_address(client_host)
            if ip.is_private or ip.is_loopback:
                response = await call_next(request)
                return response
        except ValueError:
            pass
        
        # Get rate limit for this endpoint
        path = request.url.path
        limit_config = None
        
        for route, config in self.limits.items():
            if path.startswith(route):
                limit_config = config
                break
        
        if limit_config:
            limit = limit_config["limit"]
            window = limit_config["window"]
            
            # Create a unique key for this client and endpoint
            key = f"rate_limit:{client_host}:{path}"
            
            # Get current count
            current = self.redis_client.get(key)
            current_count = int(current) if current else 0
            
            if current_count >= limit:
                # Increment rate limit exceeded metric
                rate_limit_exceeded_total.labels(
                    endpoint=path,
                    ip_address=client_host
                ).inc()
                
                # Calculate retry after
                ttl = self.redis_client.ttl(key)
                if ttl < 0:
                    ttl = window
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Limit is {limit} per {window} seconds.",
                        "retry_after": ttl,
                        "limits": self.limits
                    },
                    headers={
                        "Retry-After": str(ttl),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + ttl))
                    }
                )
            
            # Increment counter
            if current_count == 0:
                self.redis_client.setex(key, window, 1)
            else:
                self.redis_client.incr(key)
            
            # Calculate remaining requests
            remaining = limit - (current_count + 1)
            ttl = self.redis_client.ttl(key)
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + ttl))
            
            return response
        
        # No rate limit for this endpoint
        return await call_next(request)


def setup_rate_limiting(app: FastAPI, redis_url: str):
    """Set up rate limiting middleware."""
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)