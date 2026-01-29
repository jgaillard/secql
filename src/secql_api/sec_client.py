"""SEC EDGAR client for fetching company information and financial data."""
import re
from datetime import datetime
from typing import List

import httpx

from secql_api.models import Company, Financial
from secql_api.exceptions import CompanyNotFound, RateLimited
from secql_api.config import settings


class SECClient:
    """Client for fetching data from SEC EDGAR APIs."""

    BASE_URL = "https://data.sec.gov"

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": settings.sec_user_agent,
            "Accept": "application/json",
        }
        self._ticker_to_cik: dict[str, str] = {}

    def _load_ticker_mapping(self) -> None:
        """Load ticker to CIK mapping from SEC."""
        if self._ticker_to_cik:
            return

        url = "https://www.sec.gov/files/company_tickers.json"
        response = httpx.get(url, headers=self.headers, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        for entry in data.values():
            ticker = entry["ticker"].upper()
            cik = str(entry["cik_str"]).zfill(10)
            self._ticker_to_cik[ticker] = cik

    def _get_cik(self, ticker: str) -> str:
        """Get CIK for a ticker."""
        self._load_ticker_mapping()
        ticker = ticker.upper()
        if ticker not in self._ticker_to_cik:
            raise CompanyNotFound(ticker)
        return self._ticker_to_cik[ticker]

    def get_company(self, ticker: str) -> Company:
        """Fetch company info from SEC."""
        cik = self._get_cik(ticker)

        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        response = httpx.get(url, headers=self.headers, timeout=30.0)

        if response.status_code == 404:
            raise CompanyNotFound(ticker)
        if response.status_code == 429:
            raise RateLimited()
        response.raise_for_status()

        data = response.json()

        # Extract exchange info from tickers/exchanges arrays
        exchanges = data.get("exchanges", [])
        exchange = exchanges[0] if exchanges else None

        return Company(
            cik=cik,
            ticker=ticker.upper(),
            name=data.get("name", ""),
            sector=data.get("sicDescription"),
            exchange=exchange,
        )

    def get_financials(self, ticker: str, periods: int = 1) -> List[Financial]:
        """Fetch financial data from SEC XBRL API."""
        cik = self._get_cik(ticker)

        url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        response = httpx.get(url, headers=self.headers, timeout=30.0)

        if response.status_code == 404:
            raise CompanyNotFound(ticker)
        if response.status_code == 429:
            raise RateLimited()
        response.raise_for_status()

        data = response.json()
        facts = data.get("facts", {})

        # Extract key metrics from us-gaap taxonomy
        us_gaap = facts.get("us-gaap", {})

        financials = self._extract_financials(
            cik=cik,
            ticker=ticker.upper(),
            us_gaap=us_gaap,
            periods=periods,
        )

        return financials

    def _extract_financials(
        self,
        cik: str,
        ticker: str,
        us_gaap: dict,
        periods: int,
    ) -> List[Financial]:
        """Extract normalized financials from XBRL data."""

        # XBRL tag mappings (multiple possible tags for each concept)
        # Tags are ordered by preference - newer/more specific tags first
        tag_mappings = {
            "revenue": [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "TotalRevenuesAndOtherIncome",
            ],
            "net_income": [
                "NetIncomeLoss",
                "ProfitLoss",
                "NetIncomeLossAvailableToCommonStockholdersBasic",
            ],
            "total_assets": ["Assets"],
            "total_liabilities": ["Liabilities"],
            "cash_and_equivalents": [
                "CashAndCashEquivalentsAtCarryingValue",
                "Cash",
                "CashCashEquivalentsAndShortTermInvestments",
            ],
            "shares_outstanding": [
                "CommonStockSharesOutstanding",
                "WeightedAverageNumberOfSharesOutstandingBasic",
            ],
            "eps_basic": ["EarningsPerShareBasic"],
        }

        # Regex to parse frame field: CY2025Q2 (quarterly) or CY2025 (annual)
        # Also handles instant frames like CY2025Q2I
        frame_pattern = re.compile(r"^CY(\d{4})(Q(\d))?I?$")

        # Collect all periods with data
        period_data: dict[str, dict] = {}

        for field, tags in tag_mappings.items():
            for tag in tags:
                if tag not in us_gaap:
                    continue

                units = us_gaap[tag].get("units", {})
                # Try USD first, then shares, then pure
                values = (
                    units.get("USD")
                    or units.get("shares")
                    or units.get("USD/shares")
                    or []
                )

                for entry in values:
                    # Prefer using frame field for standardized period identification
                    frame = entry.get("frame")
                    if frame:
                        match = frame_pattern.match(frame)
                        if match:
                            year = match.group(1)
                            quarter = match.group(3)
                            if quarter:
                                period = f"{year}-Q{quarter}"
                                period_type = "quarterly"
                            else:
                                period = year
                                period_type = "annual"
                        else:
                            continue  # Skip non-standard frames
                    else:
                        # Fallback: use date-based calculation
                        if "end" not in entry:
                            continue

                        end_date = entry["end"]
                        start_date = entry.get("start")

                        if start_date:
                            # Duration-based (revenue, net income)
                            start = datetime.strptime(start_date, "%Y-%m-%d")
                            end = datetime.strptime(end_date, "%Y-%m-%d")
                            days = (end - start).days

                            if 80 <= days <= 100:
                                period_type = "quarterly"
                                quarter = (end.month - 1) // 3 + 1
                                period = f"{end.year}-Q{quarter}"
                            elif 350 <= days <= 380:
                                period_type = "annual"
                                period = str(end.year)
                            else:
                                continue  # Skip unusual periods
                        else:
                            # Instant values without frame - use date-based quarter
                            end = datetime.strptime(end_date, "%Y-%m-%d")
                            quarter = (end.month - 1) // 3 + 1
                            period = f"{end.year}-Q{quarter}"
                            period_type = "quarterly"

                    if period not in period_data:
                        period_data[period] = {
                            "period": period,
                            "period_type": period_type,
                        }

                    # Only set if not already set (first tag wins)
                    if field not in period_data[period]:
                        val = entry.get("val")
                        if field == "eps_basic" and val is not None:
                            period_data[period][field] = float(val)
                        elif val is not None:
                            period_data[period][field] = int(val)

                break  # Use first matching tag

        # Sort by period descending and limit
        sorted_periods = sorted(period_data.keys(), reverse=True)[:periods]

        return [
            Financial(
                cik=cik,
                ticker=ticker,
                currency="USD",
                **period_data[p],
            )
            for p in sorted_periods
        ]
