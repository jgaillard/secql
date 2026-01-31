from fastapi import FastAPI
from secql_api.routes.companies import router as companies_router
from secql_api.routes.keys import router as keys_router
from secql_api.auth import APIKeyMiddleware
from secql_api.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
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
