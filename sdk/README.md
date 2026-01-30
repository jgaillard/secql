# SecQL Python SDK

Official Python SDK for the [SecQL API](../README.md) - clean SEC EDGAR data with excellent developer experience.

## Installation

```bash
pip install secql
```

For pandas DataFrame support:

```bash
pip install secql[pandas]
```

## Quick Start

```python
from secql import SecQL

client = SecQL(api_key="your_api_key")

# Get company info
company = client.company("AAPL")
print(f"{company.name} ({company.ticker})")
# Apple Inc. (AAPL)

# Get latest financials
financials = client.financials("AAPL")
print(f"Revenue: ${financials.revenue:,}")
# Revenue: $94,930,000,000

# Get recent SEC filings
filings = client.filings("AAPL", limit=5)
for filing in filings:
    print(f"{filing.form_type} - {filing.filed_at}")
```

## Configuration

### API Key

Set your API key via constructor or environment variable:

```python
# Option 1: Constructor argument
client = SecQL(api_key="your_api_key")

# Option 2: Environment variable
# export SECQL_API_KEY=your_api_key
client = SecQL()
```

### Custom Base URL

For self-hosted or staging environments:

```python
client = SecQL(
    api_key="your_api_key",
    base_url="https://staging-api.secql.dev"
)

# Or via environment variable
# export SECQL_API_URL=https://staging-api.secql.dev
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECQL_API_KEY` | Your API key | - |
| `SECQL_API_URL` | API base URL | `https://api.secql.dev` |

## Methods

### `company(ticker: str) -> Company`

Get company profile by ticker symbol.

```python
company = client.company("MSFT")

print(company.cik)      # "0000789019"
print(company.ticker)   # "MSFT"
print(company.name)     # "Microsoft Corporation"
print(company.sector)   # "Technology"
print(company.exchange) # "NASDAQ"
```

### `financials(ticker: str, periods: int = 1, as_dataframe: bool = False)`

Get financial data for a company.

```python
# Latest quarter
latest = client.financials("AAPL")
print(latest.period)     # "2024-Q3"
print(latest.revenue)    # 94930000000
print(latest.net_income) # 21448000000

# Multiple periods
history = client.financials("AAPL", periods=4)
for f in history:
    print(f"{f.period}: ${f.revenue:,}")
```

**Available fields:**
- `cik`, `ticker`, `period`, `period_type`
- `revenue`, `net_income`
- `total_assets`, `total_liabilities`
- `cash_and_equivalents`
- `shares_outstanding`, `eps_basic`
- `currency`

### `filings(ticker: str, limit: int = 20) -> List[Filing]`

Get recent SEC filings.

```python
filings = client.filings("AAPL", limit=10)

for filing in filings:
    print(filing.form_type)       # "10-Q", "10-K", "8-K"
    print(filing.filed_at)        # "2024-11-01"
    print(filing.accession_number)
    print(filing.url)             # Direct link to SEC filing
```

## Pandas Integration

Convert financial data to pandas DataFrames for analysis:

```python
# Get historical financials as DataFrame
df = client.financials("AAPL", periods=8, as_dataframe=True)

print(df.columns)
# ['ticker', 'period', 'period_type', 'revenue', 'net_income',
#  'total_assets', 'total_liabilities', 'cash_and_equivalents',
#  'shares_outstanding', 'eps_basic']

# Calculate revenue growth
df['revenue_growth'] = df['revenue'].pct_change()

# Plot revenue over time
df.plot(x='period', y='revenue', kind='bar')
```

Requires `pip install secql[pandas]`.

## Async Client

For async applications, use `AsyncSecQL`:

```python
import asyncio
from secql import AsyncSecQL

async def main():
    async with AsyncSecQL(api_key="your_api_key") as client:
        # Fetch multiple companies concurrently
        companies = await asyncio.gather(
            client.company("AAPL"),
            client.company("MSFT"),
            client.company("GOOGL"),
        )

        for company in companies:
            print(f"{company.ticker}: {company.name}")

asyncio.run(main())
```

All methods have the same signatures as the sync client:

```python
async with AsyncSecQL() as client:
    company = await client.company("AAPL")
    financials = await client.financials("AAPL", periods=4)
    filings = await client.filings("AAPL", limit=10)
```

## Error Handling

The SDK raises specific exceptions for different error conditions:

```python
from secql import SecQL, CompanyNotFound, RateLimited, InvalidAPIKey, APIError

client = SecQL(api_key="your_api_key")

try:
    company = client.company("INVALID")
except CompanyNotFound as e:
    print(f"Ticker not found: {e.ticker}")
except RateLimited as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except InvalidAPIKey:
    print("Check your API key")
except APIError as e:
    print(f"API error ({e.status_code}): {e}")
```

### Exception Hierarchy

```
SecQLError (base)
├── CompanyNotFound   # 404 - Ticker not in SEC database
├── RateLimited       # 429 - Too many requests
├── InvalidAPIKey     # 401 - Bad or missing API key
└── APIError          # Other API errors
```

## Context Manager

Both clients support context managers for automatic cleanup:

```python
# Sync
with SecQL(api_key="your_api_key") as client:
    company = client.company("AAPL")

# Async
async with AsyncSecQL(api_key="your_api_key") as client:
    company = await client.company("AAPL")
```

## Example: Compare Big Tech Financials

```python
from secql import SecQL

client = SecQL()
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

print(f"{'Ticker':<8} {'Revenue':>15} {'Net Income':>15} {'EPS':>8}")
print("-" * 50)

for ticker in tickers:
    f = client.financials(ticker)
    print(f"{ticker:<8} ${f.revenue:>13,} ${f.net_income:>13,} ${f.eps_basic:>6.2f}")
```

## Links

- [API Documentation](../README.md)
- [Source Code](https://github.com/secql/secql-python)
- [PyPI Package](https://pypi.org/project/secql/)

## License

MIT
