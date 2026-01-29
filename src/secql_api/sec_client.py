"""SEC EDGAR client for fetching company information and financial data."""
import httpx
from secql_api.models import Company
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
