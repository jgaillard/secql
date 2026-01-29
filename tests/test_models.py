# tests/test_models.py
from secql_api.models import Company, Financial, Filing


def test_company_model():
    company = Company(
        cik="0000320193",
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        exchange="NASDAQ",
    )
    assert company.ticker == "AAPL"
    assert company.cik == "0000320193"


def test_financial_model():
    financial = Financial(
        cik="0000320193",
        ticker="AAPL",
        period="2024-Q3",
        period_type="quarterly",
        revenue=94930000000,
        net_income=21448000000,
        total_assets=364980000000,
        total_liabilities=308030000000,
        cash_and_equivalents=29965000000,
        shares_outstanding=15550000000,
        eps_basic=1.38,
        currency="USD",
    )
    assert financial.revenue == 94930000000
    assert financial.period == "2024-Q3"


def test_filing_model():
    filing = Filing(
        cik="0000320193",
        ticker="AAPL",
        form_type="10-K",
        filed_at="2024-11-01",
        accession_number="0000320193-24-000081",
        url="https://www.sec.gov/Archives/edgar/data/320193/...",
    )
    assert filing.form_type == "10-K"
