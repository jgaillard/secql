# tests/test_auth.py
from fastapi.testclient import TestClient
from secql_api.main import app
import os

client = TestClient(app)


def test_request_without_api_key_fails():
    """Requests without API key should be rejected."""
    response = client.get("/companies/AAPL")
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "missing_api_key"


def test_request_with_invalid_api_key_fails():
    """Requests with invalid API key should be rejected."""
    response = client.get(
        "/companies/AAPL",
        headers={"X-API-Key": "invalid_key_123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "invalid_api_key"


def test_request_with_valid_api_key_succeeds():
    """Requests with valid API key should succeed."""
    # Use test key from environment or default
    test_key = os.environ.get("SECQL_TEST_API_KEY", "test_key_12345")
    response = client.get(
        "/companies/AAPL",
        headers={"X-API-Key": test_key}
    )
    assert response.status_code == 200


def test_health_endpoint_no_auth_required():
    """Health endpoint should work without auth."""
    response = client.get("/health")
    assert response.status_code == 200
