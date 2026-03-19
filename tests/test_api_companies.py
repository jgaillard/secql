# tests/test_api_companies.py
import os
from fastapi.testclient import TestClient
from secql_api.main import app

client = TestClient(app)

# Use test key from environment or default
TEST_API_KEY = os.environ.get("SECQL_TEST_API_KEY", "test_key_12345")
AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}


def test_get_company():
    response = client.get("/companies/AAPL", headers=AUTH_HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["cik"] == "0000320193"
    assert "Apple" in data["name"]


def test_get_company_not_found():
    response = client.get("/companies/ZZZZZ", headers=AUTH_HEADERS)
    assert response.status_code == 404

    data = response.json()
    detail = data["detail"]
    assert detail["error"] == "company_not_found"
    assert "hint" in detail


def test_get_company_invalid_ticker():
    response = client.get("/companies/INVALIDTICKER123", headers=AUTH_HEADERS)
    assert response.status_code == 400

    data = response.json()
    detail = data["detail"]
    assert detail["error"] == "invalid_ticker"
