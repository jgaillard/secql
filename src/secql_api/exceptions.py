# src/secql_api/exceptions.py
class SecQLError(Exception):
    """Base exception for SecQL."""
    pass


class CompanyNotFound(SecQLError):
    """Company not found in SEC database."""
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f"No SEC filings found for ticker '{ticker}'")


class RateLimited(SecQLError):
    """Rate limited by SEC API."""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds")


class InvalidTicker(SecQLError):
    """Invalid ticker format."""
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f"Invalid ticker format: '{ticker}'")
