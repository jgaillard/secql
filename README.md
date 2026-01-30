# SecQL

**Clean SEC EDGAR data with excellent developer experience.**

SecQL is a REST API that transforms raw SEC EDGAR filings into structured, queryable financial data. Built for fintech engineers who need reliable company fundamentals without parsing XML.

## Quick Start

```bash
curl -H "X-API-Key: your_api_key" \
  https://api.secql.dev/companies/AAPL
```

```json
{
  "cik": "0000320193",
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "exchange": "NASDAQ"
}
```

## API Reference

### Get Company Profile

```
GET /companies/{ticker}
```

Returns company information including CIK, name, sector, and exchange.

**Example:**
```bash
curl -H "X-API-Key: $SECQL_API_KEY" \
  https://api.secql.dev/companies/MSFT
```

### Get Latest Financials

```
GET /companies/{ticker}/financials
```

Returns the most recent quarterly or annual financial data.

**Example:**
```bash
curl -H "X-API-Key: $SECQL_API_KEY" \
  https://api.secql.dev/companies/AAPL/financials
```

**Response:**
```json
{
  "cik": "0000320193",
  "ticker": "AAPL",
  "period": "2024-Q3",
  "period_type": "quarterly",
  "revenue": 94930000000,
  "net_income": 21448000000,
  "total_assets": 364980000000,
  "total_liabilities": 308030000000,
  "cash_and_equivalents": 29965000000,
  "shares_outstanding": 15287521000,
  "eps_basic": 1.40,
  "currency": "USD"
}
```

### Get Financial History

```
GET /companies/{ticker}/financials/history?periods={n}
```

Returns up to `n` periods of historical financial data (max 40).

**Example:**
```bash
curl -H "X-API-Key: $SECQL_API_KEY" \
  "https://api.secql.dev/companies/AAPL/financials/history?periods=4"
```

### Get SEC Filings

```
GET /companies/{ticker}/filings?limit={n}
```

Returns recent SEC filings with direct links to source documents (max 100).

**Example:**
```bash
curl -H "X-API-Key: $SECQL_API_KEY" \
  "https://api.secql.dev/companies/AAPL/filings?limit=5"
```

**Response:**
```json
[
  {
    "cik": "0000320193",
    "ticker": "AAPL",
    "form_type": "10-Q",
    "filed_at": "2024-11-01",
    "accession_number": "0000320193-24-000123",
    "url": "https://www.sec.gov/Archives/edgar/data/320193/..."
  }
]
```

## Authentication

All API requests require an API key passed in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your_api_key" https://api.secql.dev/companies/AAPL
```

Get your API key at [secql.dev/dashboard](https://secql.dev/dashboard).

## Rate Limiting

- **100 requests per minute** per API key
- Rate limit headers included in every response:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when the window resets

When rate limited, you'll receive a `429` response with a `Retry-After` header.

## Error Handling

All errors return structured JSON with actionable information:

```json
{
  "detail": {
    "error": "company_not_found",
    "message": "No SEC filings found for ticker 'INVALID'",
    "hint": "Check the ticker symbol or try searching by CIK",
    "docs": "https://docs.secql.dev/errors/company-not-found"
  }
}
```

| Status | Error Code | Description |
|--------|------------|-------------|
| 401 | `missing_api_key` | No API key provided |
| 401 | `invalid_api_key` | API key is invalid |
| 404 | `company_not_found` | Ticker not found in SEC database |
| 429 | `rate_limited` | Too many requests |

## Python SDK

For Python users, we offer an official SDK with sync and async clients:

```bash
pip install secql
```

```python
from secql import SecQL

client = SecQL(api_key="your_api_key")
company = client.company("AAPL")
print(company.name)  # Apple Inc.
```

See the [SDK documentation](sdk/README.md) for full details.

## Pricing

Pay-as-you-go pricing at approximately **$0.002 per request**. No monthly minimums.

## Links

- [API Documentation](https://docs.secql.dev)
- [Python SDK](sdk/README.md)
- [Dashboard](https://secql.dev/dashboard)
- [Status Page](https://status.secql.dev)

## License

MIT
