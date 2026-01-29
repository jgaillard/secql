# src/secql_api/routes/companies.py
from fastapi import APIRouter, HTTPException
from secql_api.sec_client import SECClient
from secql_api.models import Company, Financial, Filing
from secql_api.exceptions import CompanyNotFound
from typing import List

router = APIRouter(prefix="/companies", tags=["companies"])
sec_client = SECClient()


@router.get("/{ticker}", response_model=Company)
def get_company(ticker: str):
    """Get company profile by ticker symbol."""
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


@router.get("/{ticker}/financials", response_model=Financial)
def get_financials(ticker: str):
    """Get latest financial data for a company."""
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


@router.get("/{ticker}/financials/history", response_model=List[Financial])
def get_financials_history(ticker: str, periods: int = 10):
    """Get historical financial data for a company."""
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


@router.get("/{ticker}/filings", response_model=List[Filing])
def get_filings(ticker: str, limit: int = 20):
    """Get recent SEC filings for a company."""
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
