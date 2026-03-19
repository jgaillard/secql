# tests/test_sec_client_retry.py
"""Tests for SEC client retry logic."""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from secql_api.sec_client import SECClient
from secql_api.exceptions import RateLimited


@pytest.fixture
def client():
    c = SECClient()
    # Pre-populate ticker mapping so _load_ticker_mapping doesn't fire
    c._ticker_to_cik = {"AAPL": "0000320193"}
    return c


def _mock_response(status_code: int, json_data: dict = None) -> httpx.Response:
    """Create a mock httpx.Response."""
    resp = httpx.Response(
        status_code=status_code,
        json=json_data or {},
        request=httpx.Request("GET", "https://test.example.com"),
    )
    return resp


@pytest.mark.asyncio
async def test_fetch_success_on_first_try(client):
    """Successful response returns immediately without retry."""
    ok_resp = _mock_response(200, {"status": "ok"})

    with patch("secql_api.sec_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = ok_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        response = await client._fetch("https://test.example.com")
        assert response.status_code == 200
        assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_retries_on_429(client):
    """429 from SEC triggers retry, succeeds on second attempt."""
    resp_429 = _mock_response(429)
    resp_200 = _mock_response(200, {"status": "ok"})

    call_count = 0

    async def mock_get(url):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return resp_429
        return resp_200

    with patch("secql_api.sec_client.httpx.AsyncClient") as mock_cls, \
         patch("secql_api.sec_client.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        response = await client._fetch("https://test.example.com")
        assert response.status_code == 200
        assert call_count == 2


@pytest.mark.asyncio
async def test_fetch_retries_on_5xx(client):
    """5xx from SEC triggers retry."""
    resp_500 = _mock_response(500)
    resp_200 = _mock_response(200, {"status": "ok"})

    call_count = 0

    async def mock_get(url):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return resp_500
        return resp_200

    with patch("secql_api.sec_client.httpx.AsyncClient") as mock_cls, \
         patch("secql_api.sec_client.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        response = await client._fetch("https://test.example.com")
        assert response.status_code == 200
        assert call_count == 2


@pytest.mark.asyncio
async def test_fetch_raises_rate_limited_after_max_retries(client):
    """All retries exhausted on 429 raises RateLimited."""
    resp_429 = _mock_response(429)

    with patch("secql_api.sec_client.httpx.AsyncClient") as mock_cls, \
         patch("secql_api.sec_client.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.return_value = resp_429
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        with pytest.raises(RateLimited):
            await client._fetch("https://test.example.com")

        # Should have tried MAX_RETRIES + 1 times
        assert mock_client.get.call_count == 3


@pytest.mark.asyncio
async def test_fetch_raises_timeout_after_max_retries(client):
    """All retries exhausted on timeout raises the original exception."""
    with patch("secql_api.sec_client.httpx.AsyncClient") as mock_cls, \
         patch("secql_api.sec_client.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        with pytest.raises(httpx.TimeoutException):
            await client._fetch("https://test.example.com")

        assert mock_client.get.call_count == 3
