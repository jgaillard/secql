import os
from typing import List, Optional, Union
import httpx
from secql.models import Company, Financial, Filing
from secql.exceptions import (
    CompanyNotFound,
    RateLimited,
    InvalidAPIKey,
    APIError,
)


class SecQL:
    """SecQL Python SDK client."""

    DEFAULT_BASE_URL = "https://secql-production.up.railway.app"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self._api_key = api_key or os.environ.get("SECQL_API_KEY", "")
        self._base_url = (base_url or os.environ.get("SECQL_API_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"X-API-Key": self._api_key},
            timeout=timeout,
        )

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()

        try:
            error_data = response.json()
            error_code = error_data.get("error") or error_data.get("detail", {}).get("error")
            message = error_data.get("message") or error_data.get("detail", {}).get("message", "Unknown error")
        except Exception:
            error_code = "unknown"
            message = response.text

        if response.status_code == 401:
            raise InvalidAPIKey(message)
        elif response.status_code == 404 and error_code == "company_not_found":
            raise CompanyNotFound(message.split("'")[1] if "'" in message else "unknown")
        elif response.status_code == 429:
            retry_after = error_data.get("retry_after") or error_data.get("detail", {}).get("retry_after", 60)
            raise RateLimited(retry_after)
        else:
            raise APIError(message, response.status_code)

    def company(self, ticker: str) -> Company:
        """Get company profile by ticker."""
        response = self._client.get(f"/companies/{ticker}")
        data = self._handle_response(response)
        return Company(**data)

    def financials(
        self,
        ticker: str,
        periods: int = 1,
        as_dataframe: bool = False,
    ) -> Union[Financial, List[Financial], "pandas.DataFrame"]:
        """Get financial data for a company."""
        if periods == 1:
            response = self._client.get(f"/companies/{ticker}/financials")
            data = self._handle_response(response)
            result = Financial(**data)
            if as_dataframe:
                return self._to_dataframe([result])
            return result
        else:
            response = self._client.get(
                f"/companies/{ticker}/financials/history",
                params={"periods": periods},
            )
            data = self._handle_response(response)
            result = [Financial(**f) for f in data]
            if as_dataframe:
                return self._to_dataframe(result)
            return result

    def filings(self, ticker: str, limit: int = 20) -> List[Filing]:
        """Get recent SEC filings for a company."""
        response = self._client.get(
            f"/companies/{ticker}/filings",
            params={"limit": limit},
        )
        data = self._handle_response(response)
        return [Filing(**f) for f in data]

    def _to_dataframe(self, financials: List[Financial]) -> "pandas.DataFrame":
        """Convert list of Financial to pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for as_dataframe=True. "
                "Install with: pip install secql[pandas]"
            )

        records = [
            {
                "ticker": f.ticker,
                "period": f.period,
                "period_type": f.period_type,
                "revenue": f.revenue,
                "net_income": f.net_income,
                "total_assets": f.total_assets,
                "total_liabilities": f.total_liabilities,
                "cash_and_equivalents": f.cash_and_equivalents,
                "shares_outstanding": f.shares_outstanding,
                "eps_basic": f.eps_basic,
            }
            for f in financials
        ]
        return pd.DataFrame(records)

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncSecQL:
    """Async SecQL Python SDK client."""

    DEFAULT_BASE_URL = "https://secql-production.up.railway.app"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self._api_key = api_key or os.environ.get("SECQL_API_KEY", "")
        self._base_url = (base_url or os.environ.get("SECQL_API_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"X-API-Key": self._api_key},
            timeout=timeout,
        )

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()

        try:
            error_data = response.json()
            error_code = error_data.get("error") or error_data.get("detail", {}).get("error")
            message = error_data.get("message") or error_data.get("detail", {}).get("message", "Unknown error")
        except Exception:
            error_code = "unknown"
            message = response.text

        if response.status_code == 401:
            raise InvalidAPIKey(message)
        elif response.status_code == 404 and error_code == "company_not_found":
            raise CompanyNotFound(message.split("'")[1] if "'" in message else "unknown")
        elif response.status_code == 429:
            retry_after = error_data.get("retry_after") or error_data.get("detail", {}).get("retry_after", 60)
            raise RateLimited(retry_after)
        else:
            raise APIError(message, response.status_code)

    async def company(self, ticker: str) -> Company:
        """Get company profile by ticker."""
        response = await self._client.get(f"/companies/{ticker}")
        data = self._handle_response(response)
        return Company(**data)

    async def financials(
        self,
        ticker: str,
        periods: int = 1,
        as_dataframe: bool = False,
    ) -> Union[Financial, List[Financial], "pandas.DataFrame"]:
        """Get financial data for a company."""
        if periods == 1:
            response = await self._client.get(f"/companies/{ticker}/financials")
            data = self._handle_response(response)
            result = Financial(**data)
            if as_dataframe:
                return self._to_dataframe([result])
            return result
        else:
            response = await self._client.get(
                f"/companies/{ticker}/financials/history",
                params={"periods": periods},
            )
            data = self._handle_response(response)
            result = [Financial(**f) for f in data]
            if as_dataframe:
                return self._to_dataframe(result)
            return result

    async def filings(self, ticker: str, limit: int = 20) -> List[Filing]:
        """Get recent SEC filings for a company."""
        response = await self._client.get(
            f"/companies/{ticker}/filings",
            params={"limit": limit},
        )
        data = self._handle_response(response)
        return [Filing(**f) for f in data]

    def _to_dataframe(self, financials: List[Financial]) -> "pandas.DataFrame":
        """Convert list of Financial to pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for as_dataframe=True. "
                "Install with: pip install secql[pandas]"
            )

        records = [
            {
                "ticker": f.ticker,
                "period": f.period,
                "period_type": f.period_type,
                "revenue": f.revenue,
                "net_income": f.net_income,
                "total_assets": f.total_assets,
                "total_liabilities": f.total_liabilities,
                "cash_and_equivalents": f.cash_and_equivalents,
                "shares_outstanding": f.shares_outstanding,
                "eps_basic": f.eps_basic,
            }
            for f in financials
        ]
        return pd.DataFrame(records)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
