"""API Key authentication middleware for SecQL API."""
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from secql_api.db import Database

# Endpoints that don't require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/keys"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": {
                        "error": "missing_api_key",
                        "message": "API key is required",
                        "hint": "Include 'X-API-Key' header with your API key",
                        "docs": "https://docs.secql.dev/authentication",
                    }
                },
            )

        # Validate against Supabase
        key_info = Database.validate_api_key(api_key)

        if key_info is None:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": {
                        "error": "invalid_api_key",
                        "message": "Invalid API key",
                        "hint": "Check your API key at https://secql.dev/dashboard",
                        "docs": "https://docs.secql.dev/authentication",
                    }
                },
            )

        # Store key info in request state for rate limiting and usage tracking
        request.state.api_key_id = key_info.id
        request.state.api_key_tier = key_info.tier
        request.state.requests_per_minute = key_info.requests_per_minute
        request.state.request_start = time.time()

        response = await call_next(request)

        # Record usage asynchronously (non-blocking)
        try:
            response_time_ms = int((time.time() - request.state.request_start) * 1000)
            ticker = request.path_params.get("ticker") if hasattr(request, "path_params") else None
            Database.record_usage(
                api_key_id=key_info.id,
                endpoint=request.url.path,
                ticker=ticker,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )
        except Exception:
            pass  # Don't fail the request if usage tracking fails

        return response
