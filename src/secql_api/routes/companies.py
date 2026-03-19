# src/secql_api/routes/companies.py
import logging
import re

import httpx
from fastapi import APIRouter, HTTPException
from secql_api.sec_client import SECClient
from secql_api.models import Company, Financial, Filing
from secql_api.exceptions import CompanyNotFound, InvalidTicker
from typing import List

router = APIRouter(prefix="/companies", tags=["companies"])
sec_client = SECClient()
logger = logging.getLogger("secql.routes")

TICKER_PATTERN = re.compile(r"^[A-Za-z]{1,5}$")


def validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker. Raises InvalidTicker if invalid."""
    ticker = ticker.strip().upper()
    if not TICKER_PATTERN.match(ticker):
        raise InvalidTicker(ticker)
    return ticker


def handle_sec_error(e: httpx.HTTPStatusError, ticker: str):
    """Convert httpx errors to user-friendly HTTP responses."""
    status = e.response.status_code
    logger.error("SEC API error %d for ticker=%s: %s", status, ticker, str(e))
    if status >= 500:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "upstream_error",
                "message": "SEC EDGAR API is temporarily unavailable",
                "hint": "Try again in a few seconds",
            },
        )
    raise HTTPException(
        status_code=502,
        detail={
            "error": "upstream_error",
            "message": f"Unexpected SEC API response ({status})",
        },
    )


def handle_network_error(e: Exception, ticker: str):
    """Convert network/timeout errors to user-friendly HTTP responses."""
    logger.error("SEC API network error for ticker=%s: %s", ticker, str(e))
    raise HTTPException(
        status_code=502,
        detail={
            "error": "upstream_timeout",
            "message": "SEC EDGAR API is not responding. Try again shortly.",
        },
    )


@router.get("/{ticker}", response_model=Company)
def get_company(ticker: str):
    """Get company profile by ticker symbol."""
    ticker = validate_ticker(ticker)
    try:
        return sec_client.get_company(ticker)
    except CompanyNotFound as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": str(e),
                "hint": "Check the ticker symbol or try searching by CIK",
                "docs": "https://docs.secql.dev/errors/company-not-found",
            },
        )
    except httpx.HTTPStatusError as e:
        handle_sec_error(e, ticker)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        handle_network_error(e, ticker)


@router.get("/{ticker}/financials", response_model=Financial)
def get_financials(ticker: str):
    """Get latest financial data for a company."""
    ticker = validate_ticker(ticker)
    try:
        financials = sec_client.get_financials(ticker, periods=1)
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
    except CompanyNotFound as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": str(e),
                "hint": "Check the ticker symbol or try searching by CIK",
            },
        )
    except httpx.HTTPStatusError as e:
        handle_sec_error(e, ticker)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        handle_network_error(e, ticker)


@router.get("/{ticker}/financials/history", response_model=List[Financial])
def get_financials_history(ticker: str, periods: int = 10):
    """Get historical financial data for a company."""
    ticker = validate_ticker(ticker)
    periods = min(periods, 40)  # Cap at 10 years of quarters
    try:
        return sec_client.get_financials(ticker, periods=periods)
    except CompanyNotFound as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": str(e),
                "hint": "Check the ticker symbol or try searching by CIK",
            },
        )
    except httpx.HTTPStatusError as e:
        handle_sec_error(e, ticker)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        handle_network_error(e, ticker)


@router.get("/{ticker}/filings", response_model=List[Filing])
def get_filings(ticker: str, limit: int = 20):
    """Get recent SEC filings for a company."""
    ticker = validate_ticker(ticker)
    limit = min(limit, 100)  # Cap at 100
    try:
        return sec_client.get_filings(ticker, limit=limit)
    except CompanyNotFound as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": str(e),
                "hint": "Check the ticker symbol or try searching by CIK",
            },
        )
    except httpx.HTTPStatusError as e:
        handle_sec_error(e, ticker)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        handle_network_error(e, ticker)
