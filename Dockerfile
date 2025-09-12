# This docker file is intended to be used with docker compose to deploy a production
# instance of a Reflex app.

# Stage 1: init
FROM ghcr.io/astral-sh/uv:debian AS init

# Copy local context to `/app` inside container (see .dockerignore)
WORKDIR /app
COPY . .
RUN mkdir -p /app/data /app/uploaded_files

RUN uv venv

# Install app requirements and reflex inside virtualenv
RUN uv sync --frozen

# Deploy templates and prepare app
RUN uv run reflex init

# Export static copy of frontend to /app/.web/build/client
RUN uv run reflex export --frontend-only --no-zip

# Copy static files out of /app to save space in backend image
RUN mv .web/build/client /tmp/client
RUN rm -rf .web && mkdir -p .web/build
RUN mv /tmp/client .web/build/client

# Stage 2: copy artifacts into slim image 
FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app
RUN adduser --disabled-password --home /app reflex
COPY --chown=reflex --from=init /app /app
# Install libpq-dev for psycopg (skip if not using postgres).
RUN apt-get update -y && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

RUN uv build
ENV PYTHONUNBUFFERED=1

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

# Always apply migrations before starting the backend.
RUN if [ -d alembic ]; then uv run reflex db migrate; fi
CMD ["uv", "run", "--no-sync", "reflex", "run", "--env", "prod", "--backend-only"]
