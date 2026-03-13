# ==== Set base to build development and production image =====================
# System deps: nbconvert needs pandoc, neo4j driver needs libssl

# This should be something very small you should limit memory usage
FROM python:3.12-slim AS base

# Add system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    pandoc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*



# Install uv
RUN command -v uv >/dev/null 2>&1 || \
    curl -LsSf https://astral.sh/uv/install.sh | sh


ENV PATH="/root/.local/bin:$PATH"

WORKDIR /usr/askme

# Configure uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYHTON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# ==== Set Production image with core dependencies only =======================
FROM base AS production

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project 2>/dev/null || \
    uv sync --no-dev --no-install-project


COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT []

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


