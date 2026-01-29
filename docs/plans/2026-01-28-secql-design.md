# SecQL Design Document

**Date**: 2026-01-28
**Status**: Draft

## Overview

SecQL is a Python-first REST API that provides clean, normalized company fundamentals from SEC EDGAR filings. No XBRL complexity, no parsing headaches - just simple JSON responses with the metrics developers actually need.

### Target User

Fintech startup engineers building production apps (portfolio trackers, robo-advisors, stock screeners, analytics dashboards).

### Differentiator

Simplicity and developer experience. The cleanest, best-documented API in the space with an excellent Python SDK and instant onboarding.

### Business Model

Pay-as-you-go pricing at ~$0.002 per request. First 1,000 requests/month free to reduce onboarding friction.

---

## API Design

### Core Endpoints (v1)

| Endpoint | Description |
|----------|-------------|
| `GET /companies/{ticker}` | Company profile (name, CIK, sector, exchange) |
| `GET /companies/{ticker}/financials` | Latest fundamentals |
| `GET /companies/{ticker}/financials/history` | Historical quarterly/annual data |
| `GET /companies/{ticker}/filings` | Recent filing metadata |

### Sample Response (financials)

```json
{
  "ticker": "AAPL",
  "period": "2024-Q3",
  "revenue": 94930000000,
  "net_income": 21448000000,
  "total_assets": 364980000000,
  "total_liabilities": 308030000000,
  "cash_and_equivalents": 29965000000,
  "currency": "USD"
}
```

### Core Metrics (v1)

- Revenue
- Net income
- Total assets
- Total liabilities
- Cash and equivalents
- Shares outstanding
- Earnings per share (basic)

---

## Python SDK Design

### Installation

```bash
pip install secql
```

### Design Principles

- Zero configuration to start - API key via environment variable or constructor
- Return native Python types (dicts, dataclasses) and optional Pandas DataFrames
- Clear, specific exceptions (not generic errors)
- Synchronous by default, async support available

### Basic Usage

```python
from secql import SecQL

client = SecQL()  # reads SECQL_API_KEY from env

# Get latest financials
apple = client.financials("AAPL")
print(apple.revenue)  # 94930000000
print(apple.period)   # "2024-Q3"

# Get historical data as DataFrame
history = client.financials("AAPL", periods=20, as_dataframe=True)
```

### Pandas Integration

```python
df = client.financials("AAPL", periods=40, as_dataframe=True)
df["profit_margin"] = df["net_income"] / df["revenue"]
```

### Error Handling

```python
from secql.exceptions import CompanyNotFound, RateLimited, InvalidTicker

try:
    data = client.financials("INVALID")
except CompanyNotFound:
    print("Ticker not in SEC database")
except RateLimited as e:
    print(f"Retry after {e.retry_after} seconds")
```

### Async Support

```python
from secql import AsyncSecQL

async with AsyncSecQL() as client:
    apple, msft = await asyncio.gather(
        client.financials("AAPL"),
        client.financials("MSFT")
    )
```

---

## Data Architecture

### Data Flow

```
SEC EDGAR APIs ──▶ Ingestion Worker ──▶ PostgreSQL ──▶ REST API ──▶ Users
     │                    │
     │              (normalize XBRL,
     │               map to clean schema)
     │
     └── Bulk ZIP (nightly) for backfill
```

### Storage Schema

```sql
companies (cik, ticker, name, sector, exchange, updated_at)
financials (cik, period, period_type, revenue, net_income,
            total_assets, total_liabilities, cash, filed_at)
filings (cik, form_type, filed_at, accession_number, url)
```

### Refresh Strategy

- **Nightly bulk sync**: Download SEC's `companyfacts.zip`, process all companies, update stale records
- **Real-time layer** (v2): Poll SEC submissions API every few minutes for new filings
- **On-demand fallback**: If data is older than 24h and user requests it, trigger background refresh

### Normalization Rules

- Map common XBRL tags to canonical fields (e.g., `us-gaap:Revenues` → `revenue`)
- Handle fiscal year variations (convert to calendar quarters where possible)
- Store raw values + provide currency-normalized USD amounts

### Historical Depth

10 years of quarterly data (~40 periods per company)

---

## Tech Stack

### Components

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| Ingestion workers | Python scripts, Railway cron |
| Hosting | Railway |
| Documentation | Mintlify |
| Auth/API keys | Supabase Auth |
| Billing | Stripe |

### Why This Stack

- **FastAPI**: Matches Python SDK focus, excellent OpenAPI generation, async support
- **Supabase**: Familiar, handles relational data, good free tier, auth built-in
- **Railway**: Fast to deploy, handles Python well, easy cron jobs, no DevOps overhead
- **Mintlify**: Clean, modern, developer-focused documentation

---

## Developer Experience

### Documentation

- Mintlify for docs site
- Every endpoint has copy-paste examples in Python + curl
- "Get started in 60 seconds" quickstart on homepage
- Interactive API explorer

### Onboarding Flow

1. Sign up with GitHub/Google (Supabase Auth)
2. Instant API key displayed - no email verification wall
3. Copy-paste quickstart command: `pip install secql`
4. Working example in under 1 minute

### Error Responses

```json
{
  "error": "company_not_found",
  "message": "No SEC filings found for ticker 'FAKE'",
  "hint": "Check the ticker symbol or try searching by CIK",
  "docs": "https://docs.secql.dev/errors/company-not-found"
}
```

### Rate Limiting

- Return `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- 429 responses include `retry_after` in body
- SDK handles backoff automatically

### Dashboard

- Simple usage stats (requests today/month, spend)
- API key rotation
- Billing/payment (Stripe integration)

---

## MVP Scope

### Included in v1

- 4 core endpoints (company, financials, history, filings)
- ~8,000 public companies (all SEC filers)
- 10 years historical data
- Python SDK with Pandas support
- API key auth + usage tracking
- Mintlify docs with quickstart
- Pay-as-you-go billing (Stripe)
- Nightly data refresh

### Deferred to v1.1+

- Real-time filing alerts / webhooks
- TypeScript SDK (auto-generate from OpenAPI)
- Bulk export endpoints
- Segment/geographic breakdowns
- Income statement line-item details
- Custom field selection (GraphQL-style)

---

## Launch Strategy

### Naming

Decided: **SecQL**

### Pre-launch

- Build in public on Twitter/X
- Share interesting SEC data findings
- Early access waitlist

### Launch Channels

1. Hacker News (Show HN)
2. Reddit (r/algotrading, r/fintech, r/Python)
3. Product Hunt
4. Dev newsletters (Python Weekly, TLDR)

### Pricing Positioning

- $0.002/request (~$2 per 1,000 calls)
- "First 1,000 requests/month free"
- Compare to competitors on DX and price

### Success Metrics

- 100 signups in first week
- 10 developers hitting the API regularly
- First paying customer within 30 days

---

## Future Roadmap

### v1.1

- Expand to 20-30 financial metrics
- TypeScript SDK
- Webhooks for new filings

### v2

- Real-time data updates
- International filings (non-US exchanges)
- Bulk export API

### Long-term Moat

- Best docs and SDK in the space
- Community trust / word of mouth
- Comprehensive data coverage
