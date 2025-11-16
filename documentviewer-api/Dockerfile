FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

# system dependencies for opencv, tesseract, and PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .