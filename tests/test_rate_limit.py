# tests/test_rate_limit.py
from fastapi.testclient import TestClient
from secql_api.main import app
import os

client = TestClient(app)
test_key = os.environ.get("SECQL_TEST_API_KEY", "test_key_12345")
headers = {"X-API-Key": test_key}


def test_rate_limit_headers_present():
    """Response should include rate limit headers."""
    response = client.get("/companies/AAPL", headers=headers)
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_decrements():
    """Rate limit remaining should decrement with each request."""
    response1 = client.get("/companies/AAPL", headers=headers)
    remaining1 = int(response1.headers["X-RateLimit-Remaining"])

    response2 = client.get("/companies/MSFT", headers=headers)
    remaining2 = int(response2.headers["X-RateLimit-Remaining"])

    assert remaining2 < remaining1
