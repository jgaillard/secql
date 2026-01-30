from dataclasses import dataclass
from typing import Optional


@dataclass
class Company:
    cik: str
    ticker: str
    name: str
    sector: Optional[str] = None
    exchange: Optional[str] = None


@dataclass
class Financial:
    cik: str
    ticker: str
    period: str
    period_type: str
    revenue: Optional[int] = None
    net_income: Optional[int] = None
    total_assets: Optional[int] = None
    total_liabilities: Optional[int] = None
    cash_and_equivalents: Optional[int] = None
    shares_outstanding: Optional[int] = None
    eps_basic: Optional[float] = None
    currency: str = "USD"


@dataclass
class Filing:
    cik: str
    ticker: str
    form_type: str
    filed_at: str
    accession_number: str
    url: str
