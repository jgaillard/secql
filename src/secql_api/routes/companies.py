# src/secql_api/routes/companies.py
import re

from fastapi import APIRouter, HTTPException
from secql_api.sec_client import SECClient
from secql_api.models import Company, Financial, Filing
from secql_api.exceptions import InvalidTicker
from typing import List

router = APIRouter(prefix="/companies", tags=["companies"])
sec_client = SECClient()

TICKER_PATTERN = re.compile(r"^[A-Za-z]{1,5}$")


def validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker. Raises InvalidTicker if invalid."""
    ticker = ticker.strip().upper()
    if not TICKER_PATTERN.match(ticker):
        raise InvalidTicker(ticker)
    return ticker


@router.get("/{ticker}", response_model=Company)
async def get_company(ticker: str):
    """Get company profile by ticker symbol."""
    ticker = validate_ticker(ticker)
    return await sec_client.get_company(ticker)


@router.get("/{ticker}/financials", response_model=Financial)
async def get_financials(ticker: str):
    """Get latest financial data for a company."""
    ticker = validate_ticker(ticker)
    financials = await sec_client.get_financials(ticker, periods=1)
    if not financials:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "no_financial_data",
                "message": f"No financial data found for {ticker}",
                "hint": "This company may not have filed recent 10-K/10-Q reports",
            },
        )
    return financials[0]


@router.get("/{ticker}/financials/history", response_model=List[Financial])
async def get_financials_history(ticker: str, periods: int = 10):
    """Get historical financial data for a company."""
    ticker = validate_ticker(ticker)
    periods = min(periods, 40)
    return await sec_client.get_financials(ticker, periods=periods)


@router.get("/{ticker}/filings", response_model=List[Filing])
async def get_filings(ticker: str, limit: int = 20):
    """Get recent SEC filings for a company."""
    ticker = validate_ticker(ticker)
    limit = min(limit, 100)
    return await sec_client.get_filings(ticker, limit=limit)
