import pytest
import os
from secql import AsyncSecQL
from secql.exceptions import CompanyNotFound, InvalidAPIKey

API_URL = os.environ.get("SECQL_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("SECQL_API_KEY", "test_key_12345")


@pytest.fixture
async def async_client():
    client = AsyncSecQL(api_key=API_KEY, base_url=API_URL)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_async_client_init():
    """AsyncSecQL should initialize with same parameters as SecQL."""
    client = AsyncSecQL(api_key="test_key", base_url="https://api.example.com", timeout=60.0)
    assert client._api_key == "test_key"
    assert client._base_url == "https://api.example.com"
    assert client._timeout == 60.0
    await client.close()


@pytest.mark.asyncio
async def test_async_client_init_from_env(monkeypatch):
    """Client should read API key from environment."""
    monkeypatch.setenv("SECQL_API_KEY", "env_test_key")
    client = AsyncSecQL()
    assert client._api_key == "env_test_key"
    await client.close()


@pytest.mark.asyncio
async def test_async_get_company(async_client):
    """Test fetching company info asynchronously."""
    company = await async_client.company("AAPL")
    assert company.ticker == "AAPL"
    assert "Apple" in company.name


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager support."""
    async with AsyncSecQL(api_key=API_KEY, base_url=API_URL) as client:
        company = await client.company("AAPL")
        assert company.ticker == "AAPL"


@pytest.mark.asyncio
async def test_async_get_financials(async_client):
    """Test fetching latest financials asynchronously."""
    financial = await async_client.financials("AAPL")
    assert financial.ticker == "AAPL"
    # At least some financial data should be present
    has_data = any([
        financial.revenue is not None,
        financial.net_income is not None,
        financial.total_assets is not None,
        financial.total_liabilities is not None,
    ])
    assert has_data, "Expected at least some financial data to be present"


@pytest.mark.asyncio
async def test_async_get_financials_history(async_client):
    """Test fetching financial history asynchronously."""
    history = await async_client.financials("AAPL", periods=4)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_async_get_filings(async_client):
    """Test fetching filings asynchronously."""
    filings = await async_client.filings("AAPL", limit=5)
    assert len(filings) >= 1
    assert filings[0].ticker == "AAPL"
