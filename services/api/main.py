# FastAPI entrypoint - implemented in Phase 1

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from ml.retrieval.vector_store import ensure_collection
from services.api.logging_config import get_logger, setup_logging
from services.api.metrics import router as metrics_router
from services.api.middleware import LoggingMiddleware, limiter, rate_limit_exceeded_handler
from services.api.routers import documents, evaluation, feedback, search

# Set up structured logging before anything else
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs ONCE when API starts - before accepting any requests
    logger.info("api_starting", environment=os.getenv("ENVIRONMENT", "development"))
    await ensure_collection()
    logger.info("qdrant_collection_ready")
    yield
    # runs ONCE when API shuts down (cleanup goes here later)
    logger.info("api_shutdown")


app = FastAPI(
    title="DocSense API",
    description="Multi-tenant Document Q&A Platform",
    version="0.1.0",
    lifespan=lifespan,  # register the startup/shutdown handler
)

# Middleware runs around every request (order matters - first added = outermost)
app.add_middleware(LoggingMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(metrics_router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(evaluation.router)
app.include_router(feedback.router)
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
