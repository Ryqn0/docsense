import logging
import os
import sys

import structlog


def setup_logging() -> None:
    """
    Configure structlog for the application.
    - Development: colourful, readable output
    - Production: JSON output (queryable by log aggregators)
    """
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    # Configure Python's standard logging to pass through to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    shared_processors = [
        # Add log level to every event
        structlog.stdlib.add_log_level,
        # Add timestamp in ISO 8601 format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add caller info (file + line number) - useful for debugging
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    if is_production:
        # JSON output - parseable by Datadog, CloudWatch, Loki
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable coloured output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get structlog logger bound to a specific module name."""
    return structlog.get_logger(name)
