import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger
from .metrics import REQUEST_COUNT, REQUEST_LATENCY

# Create limiter - identifies users by their IP address
limiter = Limiter(key_func=get_remote_address)


def get_real_ip(request: Request) -> str:
    """Get real client IP, handling proxies and load balancers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


limiter = Limiter(key_func=get_real_ip)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return clean JSON instead of slowapi's default HTML error."""
    return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"})


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
