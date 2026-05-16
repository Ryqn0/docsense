# FastAPI entrypoint - implemented in Phase 1

import os

from fastapi import FastAPI

from services.api.routers import documents

app = FastAPI(
    title="DocSense API",
    description="Multi-tenant Document Q&A Platform",
    version="0.1.0",
)

app.include_router(documents.router)
# include_router registers all routes from the router into the main app
# The router's prefix "/documents" + route path "/upload" = GET /documents/upload


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/info")
async def info():
    return {
        "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
        "API_PORT": os.getenv("API_PORT", "8000"),
    }
