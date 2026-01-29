"""API Key authentication middleware for SecQL API."""
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# For MVP: simple static key validation
# TODO: Replace with Supabase API key lookup
VALID_API_KEYS = {
    os.environ.get("SECQL_TEST_API_KEY", "test_key_12345"),
    os.environ.get("SECQL_API_KEY", ""),
}

# Endpoints that don't require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


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

        if api_key not in VALID_API_KEYS or api_key == "":
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

        # TODO: Track usage for billing
        response = await call_next(request)
        return response
