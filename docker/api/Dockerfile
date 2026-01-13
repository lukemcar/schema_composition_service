# syntax=docker/dockerfile:1

###############################################
# Base layer — system dependencies + JDK
###############################################
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

###############################################
# Deps layer — install Python dependencies
###############################################
FROM base AS deps

WORKDIR /app

# Copy only what is needed to resolve and build the package
COPY pyproject.toml /app/
COPY app /app/app

# Install Python dependencies (production) based on pyproject.toml
RUN pip install --no-cache-dir .

###############################################
# App layer — copy full source AFTER deps
###############################################
FROM base AS app

WORKDIR /app

# Copy installed dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy full project (including migrations, design, etc.)
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]
