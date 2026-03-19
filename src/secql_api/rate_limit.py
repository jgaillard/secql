# src/secql_api/rate_limit.py
"""Rate limiting middleware for SecQL API."""
from collections import defaultdict
from threading import Lock
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter. Replace with Redis for production."""

    def __init__(self, default_requests_per_minute: int = 100):
        self.default_rpm = default_requests_per_minute
        self.window_size = 60  # seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, requests_per_minute: int | None = None) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, reset_at)."""
        now = time.time()
        window_start = now - self.window_size
        rpm = requests_per_minute or self.default_rpm

        with self._lock:
            # Clean old requests for this key
            self._requests[key] = [
                t for t in self._requests[key] if t > window_start
            ]

            # Periodic cleanup: purge keys with no recent requests
            if len(self._requests) > 1000:
                stale = [k for k, v in self._requests.items() if not v]
                for k in stale:
                    del self._requests[k]

            count = len(self._requests[key])
            remaining = max(0, rpm - count - 1)
            reset_at = int(now + self.window_size)

            if count >= rpm:
                return False, 0, reset_at

            self._requests[key].append(now)
            return True, remaining, reset_at


rate_limiter = RateLimiter(default_requests_per_minute=100)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for public endpoints
        if request.url.path in {"/", "/health", "/docs", "/openapi.json", "/redoc", "/keys"}:
            return await call_next(request)

        # Get API key and per-key rate limit from auth middleware
        api_key = request.headers.get("X-API-Key", "anonymous")
        requests_per_minute = getattr(request.state, "requests_per_minute", 100)

        allowed, remaining, reset_at = rate_limiter.is_allowed(api_key, requests_per_minute)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "error": "rate_limited",
                        "message": "Too many requests",
                        "retry_after": reset_at - int(time.time()),
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(reset_at - int(time.time())),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

        return response
