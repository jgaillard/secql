"""API key management endpoints."""
from pydantic import BaseModel, EmailStr

from fastapi import APIRouter

from secql_api.db import Database

router = APIRouter(prefix="/keys", tags=["API Keys"])


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
def create_api_key(request: CreateKeyRequest):
    """
    Create a new API key.

    **Important:** Save your API key immediately. It will only be shown once.
    """
    key_id, key = Database.create_api_key(name=request.name, email=request.email)

    return CreateKeyResponse(
        id=key_id,
        key=key,
        message="Save this key now. It will not be shown again.",
    )
