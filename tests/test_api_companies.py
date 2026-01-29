# tests/test_api_companies.py
from fastapi.testclient import TestClient
from secql_api.main import app

client = TestClient(app)


def test_get_company():
    response = client.get("/companies/AAPL")
    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["cik"] == "0000320193"
    assert "Apple" in data["name"]


def test_get_company_not_found():
    response = client.get("/companies/INVALIDTICKER123")
    assert response.status_code == 404

    data = response.json()
    detail = data["detail"]
    assert detail["error"] == "company_not_found"
    assert "hint" in detail
