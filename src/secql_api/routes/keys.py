"""API key management endpoints."""
import logging
import time
from collections import defaultdict
from threading import Lock

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, Request

from secql_api.db import Database

router = APIRouter(prefix="/keys", tags=["API Keys"])
logger = logging.getLogger("secql.keys")

# Simple IP-based rate limit for key creation: 5 keys per hour
_key_creation_log: dict[str, list[float]] = defaultdict(list)
_key_creation_lock = Lock()
MAX_KEYS_PER_HOUR = 5


def _check_key_creation_rate(ip: str) -> None:
    """Raise 429 if IP has created too many keys recently."""
    now = time.time()
    one_hour_ago = now - 3600

    with _key_creation_lock:
        _key_creation_log[ip] = [t for t in _key_creation_log[ip] if t > one_hour_ago]
        if len(_key_creation_log[ip]) >= MAX_KEYS_PER_HOUR:
            raise HTTPException(
                status_code=429,
                content={
                    "detail": {
                        "error": "rate_limited",
                        "message": f"Maximum {MAX_KEYS_PER_HOUR} API keys per hour. Try again later.",
                    }
                },
            )
        _key_creation_log[ip].append(now)


class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""

    name: str
    email: EmailStr


class CreateKeyResponse(BaseModel):
    """Response with new API key."""

    id: str
    key: str
    message: str


@router.post("", response_model=CreateKeyResponse)
def create_api_key(body: CreateKeyRequest, request: Request):
    """
    Create a new API key.

    **Important:** Save your API key immediately. It will only be shown once.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_key_creation_rate(client_ip)

    logger.info("Creating API key name=%s email=%s ip=%s", body.name, body.email, client_ip)
    try:
        key_id, key = Database.create_api_key(name=body.name, email=body.email)
    except Exception as e:
        logger.error("API key creation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "key_creation_failed",
                "message": "Failed to create API key. Please try again.",
            },
        )

    return CreateKeyResponse(
        id=key_id,
        key=key,
        message="Save this key now. It will not be shown again.",
    )
