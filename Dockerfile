# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder stage: install dependencies into a virtualenv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for psycopg2 (needs libpq + gcc to compile).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install into an isolated venv so we can copy just that into the runtime image.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Prefer the pinned lockfile for reproducible builds; fall back to requirements.txt.
COPY requirements.lock requirements.txt ./
RUN pip install -r requirements.lock

# ---------------------------------------------------------------------------
# Runtime stage: slim image with only what we need to run
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Runtime deps: libpq5 for psycopg2; openssh-client + rsync for remote operators.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 openssh-client rsync \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chmod +x /app/docker/entrypoint.sh \
    && mkdir -p /app/backend/logs \
    && chown -R app:app /app

USER app

ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Default command runs the scheduler; compose overrides this per service.
CMD ["python", "-m", "backend.scheduler.scheduler"]
