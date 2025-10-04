FROM python:3.11-slim

LABEL maintainer="Suho Trading System"
LABEL description="Polygon.io Live Collector - Real-time Forex Data"

# Set working directory
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
COPY 00-data-ingestion/polygon-live-collector/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY 00-data-ingestion/polygon-live-collector/src/ ./src/
COPY 00-data-ingestion/polygon-live-collector/config/ ./config/

# Create logs directory
RUN mkdir -p /var/log/polygon-live-collector

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Run the collector
CMD ["python3", "/app/src/main.py"]
