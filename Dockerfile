# This docker file is intended to be used with docker compose to deploy a production
# instance of a Reflex app.

# Stage 1: builder
FROM ghcr.io/astral-sh/uv:debian AS builder

# Copy local context to `/app` inside container (see .dockerignore)
WORKDIR /app
COPY . .

# Create virtual environment and install dependencies
RUN uv venv
RUN uv sync --frozen

ENV UV_NO_SYNC=1

# Deploy templates and prepare app
RUN uv run reflex init

# Install pre-cached frontend dependencies (if exist)
RUN if [ -f .web/bun.lockb ]; then cd .web && ~/.local/share/reflex/bun/bin/bun install --frozen-lockfile; fi

# Export static copy of frontend to /srv
RUN uv run reflex export --loglevel debug --frontend-only --no-zip && mv .web/build/client/* /srv/ && rm -rf .web

# Stage 2: final image
FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app
ENV UV_NO_SYNC=1

# Install libpq-dev for psycopg (skip if not using postgres)
RUN apt-get update -y && apt-get install -y caddy libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy application and virtual environment from builder
COPY --from=builder /app /app
COPY --from=builder /srv /srv

# Create data directories
RUN mkdir -p /app/data /app/uploaded_files

ENV PYTHONUNBUFFERED=1

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

RUN uv sync --frozen

# has to match the port specified in the Caddyfile
EXPOSE 8080

CMD ["sh", "-c", "[ -d alembic ] && uv run reflex db migrate; caddy start && exec uv run reflex run --env prod --backend-only"]
