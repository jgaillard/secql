class SecQLError(Exception):
    """Base exception for SecQL SDK."""
    pass


class CompanyNotFound(SecQLError):
    """Company not found in SEC database."""
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f"No SEC filings found for ticker '{ticker}'")


class RateLimited(SecQLError):
    """Rate limited by API."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds")


class InvalidAPIKey(SecQLError):
    """Invalid or missing API key."""
    pass


class APIError(SecQLError):
    """General API error."""
    def __init__(self, message: str, status_code: int):
        self.status_code = status_code
        super().__init__(message)
