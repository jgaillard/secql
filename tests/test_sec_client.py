# tests/test_sec_client.py
import pytest
from secql_api.sec_client import SECClient


@pytest.fixture
def sec_client():
    return SECClient()


def test_get_company_by_ticker(sec_client):
    """Test fetching Apple's company info from SEC."""
    company = sec_client.get_company("AAPL")
    assert company is not None
    assert company.ticker == "AAPL"
    assert company.cik == "0000320193"
    assert "Apple" in company.name


def test_get_company_not_found(sec_client):
    """Test handling of invalid ticker."""
    from secql_api.exceptions import CompanyNotFound
    with pytest.raises(CompanyNotFound):
        sec_client.get_company("INVALIDTICKER123")
