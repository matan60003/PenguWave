from fastapi import FastAPI

app = FastAPI(
    title="PenguWave API",
    description="Backend API for PenguWave Analyst Platform",
    version="0.1.0",
)

@app.get("/healthz", tags=["Health"])
async def health_check():
    """
    Standard health check endpoint for container lifecycle monitoring.
    """
    return {"status": "ok"}
