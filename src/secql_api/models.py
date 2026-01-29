# src/secql_api/models.py
from pydantic import BaseModel
from typing import Optional


class Company(BaseModel):
    cik: str
    ticker: str
    name: str
    sector: Optional[str] = None
    exchange: Optional[str] = None


class Financial(BaseModel):
    cik: str
    ticker: str
    period: str  # e.g., "2024-Q3" or "2024"
    period_type: str  # "quarterly" or "annual"
    revenue: Optional[int] = None
    net_income: Optional[int] = None
    total_assets: Optional[int] = None
    total_liabilities: Optional[int] = None
    cash_and_equivalents: Optional[int] = None
    shares_outstanding: Optional[int] = None
    eps_basic: Optional[float] = None
    currency: str = "USD"


class Filing(BaseModel):
    cik: str
    ticker: str
    form_type: str
    filed_at: str
    accession_number: str
    url: str
