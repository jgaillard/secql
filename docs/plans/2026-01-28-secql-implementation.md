# SecQL Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python-first REST API that provides clean, normalized company fundamentals from SEC EDGAR filings with an excellent Python SDK.

**Architecture:** FastAPI backend fetches and normalizes SEC EDGAR data, stores in Supabase PostgreSQL, exposes via REST endpoints. Python SDK wraps the API with Pandas support.

**Tech Stack:** FastAPI, Supabase (PostgreSQL), pytest, httpx, pandas, Railway (deployment)

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/secql_api/__init__.py`
- Create: `src/secql_api/main.py`
- Create: `tests/__init__.py`
- Create: `tests/test_health.py`

**Step 1: Initialize project structure**

```bash
cd /Users/julien/Workspace/secql
mkdir -p src/secql_api tests
touch src/secql_api/__init__.py tests/__init__.py
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "secql-api"
version = "0.1.0"
description = "SEC EDGAR API with excellent DX"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "httpx>=0.26.0",
    "supabase>=2.3.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

**Step 3: Write the failing health check test**

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from secql_api.main import app

client = TestClient(app)

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 4: Run test to verify it fails**

Run: `cd /Users/julien/Workspace/secql && pip install -e ".[dev]" && pytest tests/test_health.py -v`
Expected: FAIL (no module named secql_api.main or app not defined)

**Step 5: Write minimal FastAPI app**

```python
# src/secql_api/main.py
from fastapi import FastAPI

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add .
git commit -m "feat: initialize FastAPI project with health endpoint"
```

---

## Task 2: Database Models and Configuration

**Files:**
- Create: `src/secql_api/config.py`
- Create: `src/secql_api/models.py`
- Create: `tests/test_models.py`

**Step 1: Create config with environment variables**

```python
# src/secql_api/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    sec_user_agent: str = "SecQL API contact@secql.dev"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 2: Write the failing models test**

```python
# tests/test_models.py
from secql_api.models import Company, Financial, Filing

def test_company_model():
    company = Company(
        cik="0000320193",
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        exchange="NASDAQ",
    )
    assert company.ticker == "AAPL"
    assert company.cik == "0000320193"

def test_financial_model():
    financial = Financial(
        cik="0000320193",
        ticker="AAPL",
        period="2024-Q3",
        period_type="quarterly",
        revenue=94930000000,
        net_income=21448000000,
        total_assets=364980000000,
        total_liabilities=308030000000,
        cash_and_equivalents=29965000000,
        shares_outstanding=15550000000,
        eps_basic=1.38,
        currency="USD",
    )
    assert financial.revenue == 94930000000
    assert financial.period == "2024-Q3"

def test_filing_model():
    filing = Filing(
        cik="0000320193",
        ticker="AAPL",
        form_type="10-K",
        filed_at="2024-11-01",
        accession_number="0000320193-24-000081",
        url="https://www.sec.gov/Archives/edgar/data/320193/...",
    )
    assert filing.form_type == "10-K"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (cannot import models)

**Step 4: Write the models**

```python
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add Pydantic models for Company, Financial, Filing"
```

---

## Task 3: SEC EDGAR Client - Company Info

**Files:**
- Create: `src/secql_api/sec_client.py`
- Create: `tests/test_sec_client.py`

**Step 1: Write the failing test for fetching company info**

```python
# tests/test_sec_client.py
import pytest
from secql_api.sec_client import SECClient

@pytest.fixture
def sec_client():
    return SECClient()

def test_get_company_by_ticker(sec_client):
    """Test fetching Apple's company info from SEC."""
    company = sec_client.get_company("AAPL")
    assert company is not None
    assert company.ticker == "AAPL"
    assert company.cik == "0000320193"
    assert "Apple" in company.name

def test_get_company_not_found(sec_client):
    """Test handling of invalid ticker."""
    from secql_api.exceptions import CompanyNotFound
    with pytest.raises(CompanyNotFound):
        sec_client.get_company("INVALIDTICKER123")
```

**Step 2: Create exceptions module**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_sec_client.py -v`
Expected: FAIL (no module sec_client)

**Step 4: Write the SEC client**

```python
# src/secql_api/sec_client.py
import httpx
from typing import Optional
from secql_api.models import Company
from secql_api.exceptions import CompanyNotFound, RateLimited
from secql_api.config import settings

class SECClient:
    """Client for fetching data from SEC EDGAR APIs."""

    BASE_URL = "https://data.sec.gov"

    def __init__(self):
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_sec_client.py -v`
Expected: PASS (note: requires internet connection)

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add SEC client with company info fetching"
```

---

## Task 4: SEC Client - Financial Data

**Files:**
- Modify: `src/secql_api/sec_client.py`
- Modify: `tests/test_sec_client.py`

**Step 1: Write the failing test for financials**

```python
# Add to tests/test_sec_client.py

def test_get_financials(sec_client):
    """Test fetching Apple's financial data."""
    financials = sec_client.get_financials("AAPL", periods=4)
    assert len(financials) > 0

    latest = financials[0]
    assert latest.ticker == "AAPL"
    assert latest.revenue is not None
    assert latest.revenue > 0
    assert latest.period_type in ["quarterly", "annual"]

def test_get_financials_with_history(sec_client):
    """Test fetching multiple periods of financial data."""
    financials = sec_client.get_financials("AAPL", periods=8)
    assert len(financials) >= 4  # At least 4 quarters available
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sec_client.py::test_get_financials -v`
Expected: FAIL (get_financials not defined)

**Step 3: Add financials method to SEC client**

```python
# Add to src/secql_api/sec_client.py

from secql_api.models import Company, Financial
from typing import List

# Add this method to SECClient class:

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
        tag_mappings = {
            "revenue": [
                "Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
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

        # Collect all periods with data
        period_data: dict[str, dict] = {}

        for field, tags in tag_mappings.items():
            for tag in tags:
                if tag not in us_gaap:
                    continue

                units = us_gaap[tag].get("units", {})
                # Try USD first, then shares, then pure
                values = units.get("USD") or units.get("shares") or units.get("USD/shares") or []

                for entry in values:
                    # Skip if no end date
                    if "end" not in entry:
                        continue

                    end_date = entry["end"]
                    start_date = entry.get("start")

                    # Determine period type and label
                    if start_date:
                        # Duration-based (revenue, net income)
                        from datetime import datetime
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
                        # Instant values (assets, liabilities)
                        from datetime import datetime
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sec_client.py::test_get_financials tests/test_sec_client.py::test_get_financials_with_history -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add financial data extraction from SEC XBRL API"
```

---

## Task 5: SEC Client - Filings List

**Files:**
- Modify: `src/secql_api/sec_client.py`
- Modify: `tests/test_sec_client.py`

**Step 1: Write the failing test for filings**

```python
# Add to tests/test_sec_client.py

def test_get_filings(sec_client):
    """Test fetching Apple's recent filings."""
    filings = sec_client.get_filings("AAPL", limit=10)
    assert len(filings) > 0
    assert len(filings) <= 10

    filing = filings[0]
    assert filing.ticker == "AAPL"
    assert filing.form_type in ["10-K", "10-Q", "8-K", "4", "DEF 14A"]
    assert filing.url.startswith("https://")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sec_client.py::test_get_filings -v`
Expected: FAIL (get_filings not defined)

**Step 3: Add filings method to SEC client**

```python
# Add to src/secql_api/sec_client.py

from secql_api.models import Company, Financial, Filing

# Add this method to SECClient class:

    def get_filings(self, ticker: str, limit: int = 20) -> List[Filing]:
        """Fetch recent filings from SEC."""
        cik = self._get_cik(ticker)

        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        response = httpx.get(url, headers=self.headers, timeout=30.0)

        if response.status_code == 404:
            raise CompanyNotFound(ticker)
        if response.status_code == 429:
            raise RateLimited()
        response.raise_for_status()

        data = response.json()
        recent = data.get("filings", {}).get("recent", {})

        filings = []
        form_types = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        for i in range(min(limit, len(form_types))):
            accession = accession_numbers[i].replace("-", "")
            doc = primary_docs[i]

            filings.append(Filing(
                cik=cik,
                ticker=ticker.upper(),
                form_type=form_types[i],
                filed_at=filing_dates[i],
                accession_number=accession_numbers[i],
                url=f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{doc}",
            ))

        return filings
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sec_client.py::test_get_filings -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add filings list from SEC submissions API"
```

---

## Task 6: API Endpoints - Companies

**Files:**
- Create: `src/secql_api/routes/__init__.py`
- Create: `src/secql_api/routes/companies.py`
- Create: `tests/test_api_companies.py`
- Modify: `src/secql_api/main.py`

**Step 1: Write the failing test for company endpoint**

```python
# tests/test_api_companies.py
from fastapi.testclient import TestClient
from secql_api.main import app

client = TestClient(app)

def test_get_company():
    response = client.get("/companies/AAPL")
    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["cik"] == "0000320193"
    assert "Apple" in data["name"]

def test_get_company_not_found():
    response = client.get("/companies/INVALIDTICKER123")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "company_not_found"
    assert "hint" in data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_companies.py -v`
Expected: FAIL (404 - route not found)

**Step 3: Create the companies router**

```python
# src/secql_api/routes/__init__.py
# Empty file for package
```

```python
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
```

**Step 4: Register the router in main.py**

```python
# src/secql_api/main.py
from fastapi import FastAPI
from secql_api.routes.companies import router as companies_router

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)

app.include_router(companies_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_api_companies.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add company, financials, and filings API endpoints"
```

---

## Task 7: API Key Authentication Middleware

**Files:**
- Create: `src/secql_api/auth.py`
- Create: `tests/test_auth.py`
- Modify: `src/secql_api/main.py`

**Step 1: Write the failing test for API key auth**

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from secql_api.main import app
import os

client = TestClient(app)

def test_request_without_api_key_fails():
    """Requests without API key should be rejected."""
    response = client.get("/companies/AAPL")
    assert response.status_code == 401
    assert response.json()["error"] == "missing_api_key"

def test_request_with_invalid_api_key_fails():
    """Requests with invalid API key should be rejected."""
    response = client.get(
        "/companies/AAPL",
        headers={"X-API-Key": "invalid_key_123"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_api_key"

def test_request_with_valid_api_key_succeeds():
    """Requests with valid API key should succeed."""
    # Use test key from environment or default
    test_key = os.environ.get("SECQL_TEST_API_KEY", "test_key_12345")
    response = client.get(
        "/companies/AAPL",
        headers={"X-API-Key": test_key}
    )
    assert response.status_code == 200

def test_health_endpoint_no_auth_required():
    """Health endpoint should work without auth."""
    response = client.get("/health")
    assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth.py::test_request_without_api_key_fails -v`
Expected: FAIL (request succeeds instead of failing)

**Step 3: Create auth middleware**

```python
# src/secql_api/auth.py
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# For MVP: simple static key validation
# TODO: Replace with Supabase API key lookup
VALID_API_KEYS = {
    os.environ.get("SECQL_TEST_API_KEY", "test_key_12345"),
    os.environ.get("SECQL_API_KEY", ""),
}

# Endpoints that don't require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "missing_api_key",
                    "message": "API key is required",
                    "hint": "Include 'X-API-Key' header with your API key",
                    "docs": "https://docs.secql.dev/authentication",
                },
            )

        if api_key not in VALID_API_KEYS or api_key == "":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_api_key",
                    "message": "Invalid API key",
                    "hint": "Check your API key at https://secql.dev/dashboard",
                    "docs": "https://docs.secql.dev/authentication",
                },
            )

        # TODO: Track usage for billing
        response = await call_next(request)
        return response
```

**Step 4: Add middleware to main.py**

```python
# src/secql_api/main.py
from fastapi import FastAPI
from secql_api.routes.companies import router as companies_router
from secql_api.auth import APIKeyMiddleware

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)

app.add_middleware(APIKeyMiddleware)
app.include_router(companies_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_auth.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add API key authentication middleware"
```

---

## Task 8: Rate Limiting

**Files:**
- Create: `src/secql_api/rate_limit.py`
- Create: `tests/test_rate_limit.py`
- Modify: `src/secql_api/main.py`

**Step 1: Write the failing test for rate limiting**

```python
# tests/test_rate_limit.py
from fastapi.testclient import TestClient
from secql_api.main import app
import os

client = TestClient(app)
test_key = os.environ.get("SECQL_TEST_API_KEY", "test_key_12345")
headers = {"X-API-Key": test_key}

def test_rate_limit_headers_present():
    """Response should include rate limit headers."""
    response = client.get("/companies/AAPL", headers=headers)
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_decrements():
    """Rate limit remaining should decrement with each request."""
    response1 = client.get("/companies/AAPL", headers=headers)
    remaining1 = int(response1.headers["X-RateLimit-Remaining"])

    response2 = client.get("/companies/MSFT", headers=headers)
    remaining2 = int(response2.headers["X-RateLimit-Remaining"])

    assert remaining2 < remaining1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_rate_limit.py::test_rate_limit_headers_present -v`
Expected: FAIL (no rate limit headers)

**Step 3: Create rate limiter**

```python
# src/secql_api/rate_limit.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """Simple in-memory rate limiter. Replace with Redis for production."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, reset_at)."""
        now = time.time()
        window_start = now - self.window_size

        with self._lock:
            # Clean old requests
            self._requests[key] = [
                t for t in self._requests[key] if t > window_start
            ]

            count = len(self._requests[key])
            remaining = max(0, self.requests_per_minute - count - 1)
            reset_at = int(now + self.window_size)

            if count >= self.requests_per_minute:
                return False, 0, reset_at

            self._requests[key].append(now)
            return True, remaining, reset_at

rate_limiter = RateLimiter(requests_per_minute=100)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for public endpoints
        if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        # Use API key as rate limit key
        api_key = request.headers.get("X-API-Key", "anonymous")

        allowed, remaining, reset_at = rate_limiter.is_allowed(api_key)

        if not allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "message": "Too many requests",
                    "retry_after": reset_at - int(time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(reset_at - int(time.time())),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

        return response
```

**Step 4: Add rate limit middleware to main.py**

```python
# src/secql_api/main.py
from fastapi import FastAPI
from secql_api.routes.companies import router as companies_router
from secql_api.auth import APIKeyMiddleware
from secql_api.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)

# Order matters: rate limit first, then auth
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)
app.include_router(companies_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_rate_limit.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add rate limiting with headers"
```

---

## Task 9: Python SDK - Core Client

**Files:**
- Create: `sdk/secql/__init__.py`
- Create: `sdk/secql/client.py`
- Create: `sdk/secql/models.py`
- Create: `sdk/secql/exceptions.py`
- Create: `sdk/pyproject.toml`
- Create: `sdk/tests/__init__.py`
- Create: `sdk/tests/test_client.py`

**Step 1: Set up SDK package structure**

```bash
mkdir -p sdk/secql sdk/tests
touch sdk/secql/__init__.py sdk/tests/__init__.py
```

**Step 2: Create SDK pyproject.toml**

```toml
# sdk/pyproject.toml
[project]
name = "secql"
version = "0.1.0"
description = "Python SDK for SecQL - SEC EDGAR API with excellent DX"
requires-python = ">=3.9"
dependencies = [
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
pandas = ["pandas>=2.0.0"]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pandas>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create SDK exceptions**

```python
# sdk/secql/exceptions.py
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
```

**Step 4: Create SDK models**

```python
# sdk/secql/models.py
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
```

**Step 5: Write the failing test for SDK client**

```python
# sdk/tests/test_client.py
import pytest
import os
from secql import SecQL
from secql.exceptions import CompanyNotFound, InvalidAPIKey

# These tests require a running API server
# Set SECQL_API_URL and SECQL_API_KEY environment variables

API_URL = os.environ.get("SECQL_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("SECQL_API_KEY", "test_key_12345")

@pytest.fixture
def client():
    return SecQL(api_key=API_KEY, base_url=API_URL)

def test_client_init_from_env(monkeypatch):
    """Client should read API key from environment."""
    monkeypatch.setenv("SECQL_API_KEY", "env_test_key")
    client = SecQL()
    assert client._api_key == "env_test_key"

def test_get_company(client):
    """Test fetching company info."""
    company = client.company("AAPL")
    assert company.ticker == "AAPL"
    assert "Apple" in company.name

def test_get_financials(client):
    """Test fetching latest financials."""
    financial = client.financials("AAPL")
    assert financial.ticker == "AAPL"
    assert financial.revenue is not None

def test_get_financials_history(client):
    """Test fetching financial history."""
    history = client.financials("AAPL", periods=4)
    assert len(history) >= 1
```

**Step 6: Run test to verify it fails**

Run: `cd sdk && pip install -e ".[dev]" && pytest tests/test_client.py -v`
Expected: FAIL (no module secql)

**Step 7: Create the SDK client**

```python
# sdk/secql/client.py
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

    DEFAULT_BASE_URL = "https://api.secql.dev"

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
        """Get financial data for a company.

        Args:
            ticker: Stock ticker symbol
            periods: Number of periods to fetch (1 for latest only)
            as_dataframe: Return as pandas DataFrame (requires pandas)

        Returns:
            Single Financial if periods=1, list otherwise, or DataFrame if as_dataframe=True
        """
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
```

**Step 8: Create SDK __init__.py**

```python
# sdk/secql/__init__.py
from secql.client import SecQL
from secql.models import Company, Financial, Filing
from secql.exceptions import (
    SecQLError,
    CompanyNotFound,
    RateLimited,
    InvalidAPIKey,
    APIError,
)

__version__ = "0.1.0"
__all__ = [
    "SecQL",
    "Company",
    "Financial",
    "Filing",
    "SecQLError",
    "CompanyNotFound",
    "RateLimited",
    "InvalidAPIKey",
    "APIError",
]
```

**Step 9: Run tests (requires running API server)**

Run: `cd /Users/julien/Workspace/secql && uvicorn secql_api.main:app --reload &`
Then: `cd sdk && pytest tests/test_client.py -v`
Expected: PASS

**Step 10: Commit**

```bash
git add .
git commit -m "feat: add Python SDK with sync client and pandas support"
```

---

## Task 10: Async SDK Client

**Files:**
- Modify: `sdk/secql/client.py`
- Modify: `sdk/secql/__init__.py`
- Create: `sdk/tests/test_async_client.py`

**Step 1: Write the failing test for async client**

```python
# sdk/tests/test_async_client.py
import pytest
import os
from secql import AsyncSecQL
from secql.exceptions import CompanyNotFound

API_URL = os.environ.get("SECQL_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("SECQL_API_KEY", "test_key_12345")

@pytest.mark.asyncio
async def test_async_get_company():
    """Test async fetching company info."""
    async with AsyncSecQL(api_key=API_KEY, base_url=API_URL) as client:
        company = await client.company("AAPL")
        assert company.ticker == "AAPL"
        assert "Apple" in company.name

@pytest.mark.asyncio
async def test_async_get_financials():
    """Test async fetching financials."""
    async with AsyncSecQL(api_key=API_KEY, base_url=API_URL) as client:
        financial = await client.financials("AAPL")
        assert financial.ticker == "AAPL"
        assert financial.revenue is not None

@pytest.mark.asyncio
async def test_async_concurrent_requests():
    """Test concurrent requests."""
    import asyncio
    async with AsyncSecQL(api_key=API_KEY, base_url=API_URL) as client:
        apple, msft = await asyncio.gather(
            client.company("AAPL"),
            client.company("MSFT"),
        )
        assert apple.ticker == "AAPL"
        assert msft.ticker == "MSFT"
```

**Step 2: Run test to verify it fails**

Run: `cd sdk && pytest tests/test_async_client.py -v`
Expected: FAIL (no AsyncSecQL)

**Step 3: Add AsyncSecQL to client.py**

```python
# Add to sdk/secql/client.py after SecQL class:

class AsyncSecQL:
    """Async SecQL Python SDK client."""

    DEFAULT_BASE_URL = "https://api.secql.dev"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self._api_key = api_key or os.environ.get("SECQL_API_KEY", "")
        self._base_url = (base_url or os.environ.get("SECQL_API_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"X-API-Key": self._api_key},
                timeout=self._timeout,
            )
        return self._client

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
        client = await self._get_client()
        response = await client.get(f"/companies/{ticker}")
        data = self._handle_response(response)
        return Company(**data)

    async def financials(
        self,
        ticker: str,
        periods: int = 1,
        as_dataframe: bool = False,
    ) -> Union[Financial, List[Financial], "pandas.DataFrame"]:
        """Get financial data for a company."""
        client = await self._get_client()

        if periods == 1:
            response = await client.get(f"/companies/{ticker}/financials")
            data = self._handle_response(response)
            result = Financial(**data)
            if as_dataframe:
                return self._to_dataframe([result])
            return result
        else:
            response = await client.get(
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
        client = await self._get_client()
        response = await client.get(
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
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

**Step 4: Update SDK __init__.py**

```python
# sdk/secql/__init__.py
from secql.client import SecQL, AsyncSecQL
from secql.models import Company, Financial, Filing
from secql.exceptions import (
    SecQLError,
    CompanyNotFound,
    RateLimited,
    InvalidAPIKey,
    APIError,
)

__version__ = "0.1.0"
__all__ = [
    "SecQL",
    "AsyncSecQL",
    "Company",
    "Financial",
    "Filing",
    "SecQLError",
    "CompanyNotFound",
    "RateLimited",
    "InvalidAPIKey",
    "APIError",
]
```

**Step 5: Run tests**

Run: `cd sdk && pytest tests/test_async_client.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add async SDK client with context manager support"
```

---

## Task 11: Create README and Documentation

**Files:**
- Create: `README.md`
- Create: `sdk/README.md`

**Step 1: Create main README**

```markdown
# SecQL

Clean SEC EDGAR data with excellent developer experience.

## Overview

SecQL provides a simple REST API for accessing SEC EDGAR financial data. No XBRL complexity, no parsing headaches - just clean JSON responses.

## Quick Start

### Using the Python SDK

```bash
pip install secql
```

```python
from secql import SecQL

client = SecQL()  # reads SECQL_API_KEY from env

# Get company info
apple = client.company("AAPL")
print(f"{apple.name} ({apple.ticker})")

# Get latest financials
financials = client.financials("AAPL")
print(f"Revenue: ${financials.revenue:,}")

# Get historical data as DataFrame
import pandas as pd
df = client.financials("AAPL", periods=20, as_dataframe=True)
df["profit_margin"] = df["net_income"] / df["revenue"]
```

### Using the REST API

```bash
curl -H "X-API-Key: your_key" https://api.secql.dev/companies/AAPL/financials
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /companies/{ticker}` | Company profile |
| `GET /companies/{ticker}/financials` | Latest financials |
| `GET /companies/{ticker}/financials/history` | Historical data |
| `GET /companies/{ticker}/filings` | Recent SEC filings |

## Development

### Running locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the API
uvicorn secql_api.main:app --reload

# Run tests
pytest
```

## License

MIT
```

**Step 2: Create SDK README**

```markdown
# SecQL Python SDK

Python SDK for the SecQL API - clean SEC EDGAR data with excellent DX.

## Installation

```bash
pip install secql

# With pandas support
pip install secql[pandas]
```

## Usage

### Basic Usage

```python
from secql import SecQL

# Initialize (reads SECQL_API_KEY from environment)
client = SecQL()

# Or pass explicitly
client = SecQL(api_key="your_api_key")

# Get company info
company = client.company("AAPL")
print(company.name)  # Apple Inc.

# Get latest financials
financials = client.financials("AAPL")
print(financials.revenue)  # 94930000000
```

### Historical Data

```python
# Get last 20 quarters
history = client.financials("AAPL", periods=20)
for f in history:
    print(f"{f.period}: ${f.revenue:,}")
```

### Pandas Integration

```python
# Get data as DataFrame
df = client.financials("AAPL", periods=40, as_dataframe=True)

# Easy analysis
df["profit_margin"] = df["net_income"] / df["revenue"]
df["profit_margin"].plot()
```

### Async Support

```python
from secql import AsyncSecQL
import asyncio

async def main():
    async with AsyncSecQL() as client:
        apple, msft = await asyncio.gather(
            client.financials("AAPL"),
            client.financials("MSFT"),
        )
        print(f"Apple revenue: ${apple.revenue:,}")
        print(f"Microsoft revenue: ${msft.revenue:,}")

asyncio.run(main())
```

### Error Handling

```python
from secql import SecQL
from secql.exceptions import CompanyNotFound, RateLimited

client = SecQL()

try:
    data = client.financials("INVALID")
except CompanyNotFound as e:
    print(f"Company not found: {e.ticker}")
except RateLimited as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

## License

MIT
```

**Step 3: Commit**

```bash
git add .
git commit -m "docs: add README files for API and SDK"
```

---

## Summary

This plan covers the MVP:

1. **Tasks 1-2**: Project setup, models, configuration
2. **Tasks 3-5**: SEC EDGAR client (company, financials, filings)
3. **Task 6**: REST API endpoints
4. **Tasks 7-8**: Authentication and rate limiting
5. **Tasks 9-10**: Python SDK (sync and async)
6. **Task 11**: Documentation

### Not in this plan (v1.1+):

- Supabase database persistence (currently fetches live from SEC)
- Stripe billing integration
- Mintlify documentation site
- Railway deployment configuration
- Nightly data sync workers

### To run the complete test suite:

```bash
cd /Users/julien/Workspace/secql
pip install -e ".[dev]"
pytest
```
