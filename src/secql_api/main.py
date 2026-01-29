from fastapi import FastAPI

app = FastAPI(
    title="SecQL API",
    description="Clean SEC EDGAR data with excellent DX",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
