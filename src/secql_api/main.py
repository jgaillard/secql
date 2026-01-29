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
