FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .