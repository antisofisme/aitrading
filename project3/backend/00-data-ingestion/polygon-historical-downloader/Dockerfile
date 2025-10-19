FROM python:3.11-slim

LABEL maintainer="Suho Trading System"
LABEL description="Polygon.io Historical Downloader - Gap Detection & Backfill"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Central Hub SDK first
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk

# Copy requirements
COPY 00-data-ingestion/polygon-historical-downloader/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY 00-data-ingestion/polygon-historical-downloader/src/ ./src/
COPY 00-data-ingestion/polygon-historical-downloader/config/ ./config/

# Copy shared utilities (ConfigClient, etc.)
COPY shared/ ./shared/

# Create logs directory
RUN mkdir -p /var/log/polygon-historical-downloader

# Copy healthcheck script
COPY 00-data-ingestion/polygon-historical-downloader/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Configure health check - verifies all dependencies
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Run the downloader
CMD ["python3", "/app/src/main.py"]
