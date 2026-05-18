import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger
from .metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Runs around every HTTP request.
    Logs structured data about each request + response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate a unique ID for this request - useful for tracing
        request_id = str(uuid.uuid4()).replace("-", "")[:8]  # short version for readability

        # Extract tenant from header (safe - returns None if missing)
        tenant_id = request.headers.get("x-tenant-id", "anonymous")

        # Record start time
        start_time = time.perf_counter()

        # Log the incoming request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            tenant_id=tenant_id,
        )

        # Call the actual endpoint
        try:
            response = await call_next(request)
            status_code = response.status_code
            level = "warning" if status_code >= 400 else "info"
        except Exception as e:
            # Unexpected crash - log at error level
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                tenant_id=tenant_id,
                latency_ms=elapsed_ms,
                error=str(e),
            )
            raise

        # Calculate latency
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Increment Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status_code=str(status_code)
        ).inc()

        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(
            elapsed_ms / 1000
        )  # convert ms into seconds

        # Log the completed request
        log_fn = getattr(logger, level)
        log_fn(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            tenant_id=tenant_id,
            status_code=status_code,
            latency_ms=elapsed_ms,
        )

        # Add request ID to response headers - useful for debugging
        response.headers["X-Request-ID"] = request_id
        return response
