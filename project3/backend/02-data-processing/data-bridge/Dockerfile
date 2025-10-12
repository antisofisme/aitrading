FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Central Hub SDK
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Copy requirements and install Python dependencies
COPY 02-data-processing/data-bridge/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY 02-data-processing/data-bridge/src/ ./src/
COPY 02-data-processing/data-bridge/config/ ./config/

# Copy Central Hub shared components
COPY 01-core-infrastructure/central-hub/shared/ ./shared/

# Create logs directory
RUN mkdir -p /app/logs

# Copy healthcheck script
COPY 02-data-processing/data-bridge/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Configure health check - verifies all dependencies
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=3 \
  CMD /app/healthcheck.sh

# Set Python path for shared utilities access
ENV PYTHONPATH="/app"

WORKDIR /app/src

CMD ["python3", "main.py"]
