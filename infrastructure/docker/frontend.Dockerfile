FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY services/frontend ./services/frontend

ENV PATH="/app/.venv/bin:$PATH"

CMD ["streamlit", "run", "services/frontend/main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
