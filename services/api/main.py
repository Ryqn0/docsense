# FastAPI entrypoint - implemented in Phase 1

import os

from fastapi import FastAPI

app = FastAPI(
    title="DocSense API",
    description="Multi-tenant Document Q&A Platform",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/info")
async def info():
    return {
        "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
        "API_PORT": os.getenv("API_PORT", "8000"),
    }
