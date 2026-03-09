"""
Rate limiting configuration for FastAPI application.

This module provides rate limiting functionality to prevent API abuse
and control billing costs by limiting the number of requests per client.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.frameworks.settings import Settings
import os

settings = Settings()

# Get rate limiter storage from environment
# For single Cloud Run instance (recommended for cost-effective setups): use "memory://"
# Only use Redis if you have multiple instances running simultaneously and need shared state
# Default to memory storage - perfect for single-instance Cloud Run deployments
RATE_LIMITER_STORAGE = os.getenv("RATE_LIMITER_STORAGE", "memory://")
RATE_LIMITER_DEFAULT_LIMIT = os.getenv("RATE_LIMITER_DEFAULT_LIMIT", "1000/hour")

# Initialize rate limiter
# Using in-memory storage - works perfectly for single-instance Cloud Run
# Only switch to Redis if you scale to multiple concurrent instances
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=[RATE_LIMITER_DEFAULT_LIMIT],  # Default limit from env or 1000/hour
    storage_uri=RATE_LIMITER_STORAGE,  # Storage backend (memory:// for single instance, redis:// for multiple)
    headers_enabled=True,  # Enable rate limit headers in responses
)

# Rate limit configurations
# Format: "number/period" where period can be: second, minute, hour, day
RATE_LIMITS = {
    # Authentication endpoints - stricter limits to prevent brute force
    "auth": {
        "register": "5/minute",  # Prevent spam registrations
        "login": "10/minute",  # Prevent brute force attacks
        "password_reset": "3/hour",  # Prevent abuse of password reset
        "refresh": "30/minute",  # Allow reasonable refresh rate
        "default": "20/minute",  # Default for other auth endpoints
    },
    # General API endpoints
    "api": {
        "read": "200/hour",  # Read operations (GET)
        "write": "100/hour",  # Write operations (POST, PUT, PATCH, DELETE)
        "default": "150/hour",  # Default for other endpoints
    },
    # Health check endpoints - more lenient
    "health": {
        "default": "60/minute",
    },
    # Documentation endpoints - lenient
    "docs": {
        "default": "100/hour",
    },
}


def get_rate_limit_key(request: Request) -> str:
    """Get a custom key for rate limiting.
    
    Can be extended to use user ID for authenticated users,
    allowing higher limits for authenticated vs anonymous users.
    """
    # Try to get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with a clear error message."""
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}. Please try again later.",
            "retry_after": exc.retry_after,
        },
    )
    return response


# Decorator helpers for common rate limits
def rate_limit_auth(limit: str = None):
    """Rate limit decorator for authentication endpoints."""
    limit = limit or RATE_LIMITS["auth"]["default"]
    return limiter.limit(limit)


def rate_limit_api(limit: str = None):
    """Rate limit decorator for general API endpoints."""
    limit = limit or RATE_LIMITS["api"]["default"]
    return limiter.limit(limit)


def rate_limit_read(limit: str = None):
    """Rate limit decorator for read operations."""
    limit = limit or RATE_LIMITS["api"]["read"]
    return limiter.limit(limit)


def rate_limit_write(limit: str = None):
    """Rate limit decorator for write operations."""
    limit = limit or RATE_LIMITS["api"]["write"]
    return limiter.limit(limit)

