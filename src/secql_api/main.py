import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from secql_api.routes.companies import router as companies_router
from secql_api.routes.keys import router as keys_router
from secql_api.auth import APIKeyMiddleware
from secql_api.rate_limit import RateLimitMiddleware
import httpx

from secql_api.exceptions import RateLimited, CompanyNotFound, InvalidTicker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("secql")

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)


# --- Global exception handlers ---

@app.exception_handler(RateLimited)
async def rate_limited_handler(request: Request, exc: RateLimited):
    logger.warning("SEC rate limit hit for %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "error": "upstream_rate_limited",
                "message": "SEC EDGAR API rate limit reached. Try again shortly.",
                "retry_after": exc.retry_after,
            }
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(InvalidTicker)
async def invalid_ticker_handler(request: Request, exc: InvalidTicker):
    return JSONResponse(
        status_code=400,
        content={
            "detail": {
                "error": "invalid_ticker",
                "message": str(exc),
                "hint": "Ticker must be 1-5 alphanumeric characters (e.g., AAPL, MSFT)",
            }
        },
    )


@app.exception_handler(CompanyNotFound)
async def company_not_found_handler(request: Request, exc: CompanyNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "detail": {
                "error": "company_not_found",
                "message": str(exc),
                "hint": "Check the ticker symbol or try searching by CIK",
                "docs": "https://docs.secql.dev/errors/company-not-found",
            }
        },
    )


@app.exception_handler(httpx.HTTPStatusError)
async def http_status_error_handler(request: Request, exc: httpx.HTTPStatusError):
    status = exc.response.status_code
    logger.error("SEC API error %d for %s: %s", status, request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "detail": {
                "error": "upstream_error",
                "message": "SEC EDGAR API is temporarily unavailable"
                if status >= 500
                else f"Unexpected SEC API response ({status})",
                "hint": "Try again in a few seconds",
            }
        },
    )


@app.exception_handler(httpx.TimeoutException)
async def timeout_handler(request: Request, exc: httpx.TimeoutException):
    logger.error("SEC API timeout for %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "detail": {
                "error": "upstream_timeout",
                "message": "SEC EDGAR API is not responding. Try again shortly.",
            }
        },
    )


@app.exception_handler(httpx.ConnectError)
async def connect_error_handler(request: Request, exc: httpx.ConnectError):
    logger.error("SEC API connection error for %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "detail": {
                "error": "upstream_timeout",
                "message": "SEC EDGAR API is not responding. Try again shortly.",
            }
        },
    )


# Order matters: rate limit first, then auth
# (last added = first executed in middleware stack)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)
app.include_router(companies_router)
app.include_router(keys_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "name": "SecQL API",
        "version": "0.1.0",
        "docs": "https://secql.dev",
        "health": "/health",
    }
