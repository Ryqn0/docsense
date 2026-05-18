from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter(tags=["observability"])

# --- Define metrics ---

REQUEST_COUNT = Counter(
    "docsense_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    # labelness * each unique combination gets its own counter
    # e.g. POST /search/ 200, POST /search/ 500, GET /health 200
)

REQUEST_LATENCY = Histogram(
    "docsense_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    # buckets define latency thresholds for the histogram
    # tells you: "X% of requests finish under 0.5s"
)

DOCUMENTS_UPLOADED = Counter(
    "docsense_documents_uploaded_total", "Total documents successfully uploaded"
)

CHUNKS_CREATED = Counter("docsense_chunks_created_total", "Total chunks created from documents")

SEARCH_REQUESTS = Counter("docsense_search_requests_total", "Total search requests", ["tenant_id"])

FEEDBACK_SUBMITTED = Counter(
    "docsense_feedback_total",
    "Total feedback submissions",
    ["rating"],  # label: "1" or "-1"
)


@router.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    Prometheus server scrapes this endpoint periodically.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
