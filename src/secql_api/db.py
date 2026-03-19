# src/secql_api/db.py
"""Supabase database client for API key management."""
import logging
from typing import Optional
from dataclasses import dataclass

from supabase import create_client, Client

from secql_api.config import settings

logger = logging.getLogger("secql.db")


@dataclass
class APIKeyInfo:
    """Validated API key information."""

    id: str
    tier: str
    requests_per_minute: int


class Database:
    """Supabase database client."""

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._client is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise RuntimeError("Supabase credentials not configured")
            cls._client = create_client(settings.supabase_url, settings.supabase_key)
        return cls._client

    @classmethod
    def validate_api_key(cls, key: str) -> Optional[APIKeyInfo]:
        """Validate an API key and return its info."""
        # Allow test key in development
        if settings.secql_test_api_key and key == settings.secql_test_api_key:
            return APIKeyInfo(id="test", tier="free", requests_per_minute=100)

        try:
            client = cls.get_client()
            result = client.rpc("validate_api_key", {"p_key": key}).execute()

            if result.data and len(result.data) > 0:
                row = result.data[0]
                return APIKeyInfo(
                    id=row["id"],
                    tier=row["tier"],
                    requests_per_minute=row["requests_per_minute"],
                )
        except Exception as e:
            logger.error("API key validation failed: %s", e)

        return None

    @classmethod
    def record_usage(
        cls,
        api_key_id: str,
        endpoint: str,
        ticker: Optional[str],
        status_code: int,
        response_time_ms: int,
    ) -> None:
        """Record API usage for billing."""
        # Skip recording for test key
        if api_key_id == "test":
            return

        try:
            client = cls.get_client()
            client.rpc(
                "record_usage",
                {
                    "p_api_key_id": api_key_id,
                    "p_endpoint": endpoint,
                    "p_ticker": ticker,
                    "p_status_code": status_code,
                    "p_response_time_ms": response_time_ms,
                },
            ).execute()
        except Exception as e:
            logger.warning("Usage recording failed for key=%s: %s", api_key_id, e)

    @classmethod
    def create_api_key(cls, name: str, email: str) -> tuple[str, str]:
        """Create a new API key. Returns (id, key)."""
        client = cls.get_client()
        result = client.rpc("create_api_key", {"p_name": name, "p_email": email}).execute()

        if result.data and len(result.data) > 0:
            row = result.data[0]
            return row["id"], row["key"]

        raise RuntimeError("Failed to create API key")
