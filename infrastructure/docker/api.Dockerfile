# Base image - slim = no dev tools, smaller surface area
FROM python:3.12-slim

# Install uv from its official image (no pip needed)
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app

# Layer cache: deps change rarely, code changes constantly
COPY pyproject.toml uv.lock ./

# Install only production deps (no ruff, pre-commit, pytest in the container)
RUN uv sync --frozen --no-dev

COPY services/api ./services/api
# /app/services/api/main.py

COPY ml ./ml

COPY data/eval_sets ./data/eval_sets

COPY alembic.ini .
COPY alembic ./alembic

# Add venv to PATH so uvicorn is found without activating
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "services.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload"]
