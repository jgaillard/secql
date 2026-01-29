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


def test_get_financials(sec_client):
    """Test fetching Apple's financial data."""
    financials = sec_client.get_financials("AAPL", periods=4)
    assert len(financials) > 0

    latest = financials[0]
    assert latest.ticker == "AAPL"
    assert latest.period_type in ["quarterly", "annual"]

    # Find a period with revenue (not all periods have revenue due to SEC reporting)
    periods_with_revenue = [f for f in financials if f.revenue is not None]
    assert len(periods_with_revenue) > 0, "Expected at least one period with revenue data"
    assert periods_with_revenue[0].revenue > 0


def test_get_financials_with_history(sec_client):
    """Test fetching multiple periods of financial data."""
    financials = sec_client.get_financials("AAPL", periods=8)
    assert len(financials) >= 4  # At least 4 quarters available
