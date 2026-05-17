# FastAPI entrypoint - implemented in Phase 1

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ml.retrieval.vector_store import ensure_collection
from services.api.routers import documents, evaluation, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs ONCE when API starts - before accepting any requests
    await ensure_collection()
    yield
    # runs ONCE when API shuts down (cleanup goes here later)


app = FastAPI(
    title="DocSense API",
    description="Multi-tenant Document Q&A Platform",
    version="0.1.0",
    lifespan=lifespan,  # register the startup/shutdown handler
)

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(evaluation.router)
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
