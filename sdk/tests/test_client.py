import pytest
import os
from secql import SecQL
from secql.exceptions import CompanyNotFound, InvalidAPIKey

API_URL = os.environ.get("SECQL_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("SECQL_API_KEY", "test_key_12345")


@pytest.fixture
def client():
    return SecQL(api_key=API_KEY, base_url=API_URL)


def test_client_init_from_env(monkeypatch):
    """Client should read API key from environment."""
    monkeypatch.setenv("SECQL_API_KEY", "env_test_key")
    client = SecQL()
    assert client._api_key == "env_test_key"


def test_get_company(client):
    """Test fetching company info."""
    company = client.company("AAPL")
    assert company.ticker == "AAPL"
    assert "Apple" in company.name


def test_get_financials(client):
    """Test fetching latest financials."""
    financial = client.financials("AAPL")
    assert financial.ticker == "AAPL"
    # At least some financial data should be present (revenue may be None for some periods)
    has_data = any([
        financial.revenue is not None,
        financial.net_income is not None,
        financial.total_assets is not None,
        financial.total_liabilities is not None,
    ])
    assert has_data, "Expected at least some financial data to be present"


def test_get_financials_history(client):
    """Test fetching financial history."""
    history = client.financials("AAPL", periods=4)
    assert len(history) >= 1
