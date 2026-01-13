# syntax=docker/dockerfile:1

###############################################
# Base layer — system dependencies
###############################################
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


###############################################
# Deps layer — install Python dependencies
###############################################
FROM base AS deps

WORKDIR /app

# Copy minimal files needed to resolve dependencies
COPY pyproject.toml /app/
COPY app /app/app

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir .


###############################################
# App layer — final runtime image
###############################################
FROM base AS worker

WORKDIR /app

# Copy installed dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy the entire project (Celery tasks, config, schemas, etc.)
COPY . /app

# Celery Worker Entrypoint
#
# `-A app.core.celery_app.celery_app` → points to your shared Celery instance
# `--loglevel=info` → readable logs
#
CMD ["celery", "-A", "app.core.celery_app.celery_app", "worker", "--loglevel=info"]
