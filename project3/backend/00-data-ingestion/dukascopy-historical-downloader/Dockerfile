# Dukascopy Historical Downloader - Dockerfile
FROM python:3.11-slim

LABEL maintainer="Suho Trading System"
LABEL description="Dukascopy Historical Downloader - Swiss Bank Grade Tick Data"

# Set working directory
WORKDIR /app

# Install system dependencies (removed WARP - using external warp-docker service)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    liblzma-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Central Hub SDK first
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk

# Copy requirements
COPY 00-data-ingestion/dukascopy-historical-downloader/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY 00-data-ingestion/dukascopy-historical-downloader/src/ /app/src/
COPY 00-data-ingestion/dukascopy-historical-downloader/config/ /app/config/

# Copy shared utilities
COPY 01-core-infrastructure/central-hub/shared/ /app/shared/

# Create log directory
RUN mkdir -p /var/log/dukascopy

# Create data directory for period tracker
RUN mkdir -p /data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check - Use proper health check script
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 /app/src/healthcheck.py

# Run service directly (proxy configured via environment variables in docker-compose)
CMD ["python3", "/app/src/main.py"]
