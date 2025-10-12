FROM python:3.11-slim

WORKDIR /app

# Install Central Hub SDK first
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Install dependencies
COPY 02-data-processing/tick-aggregator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy config and source
COPY 02-data-processing/tick-aggregator/config/ /app/config/
COPY 02-data-processing/tick-aggregator/src/ /app/src/

# Copy shared schemas
COPY 01-core-infrastructure/central-hub/shared/ /app/shared/

# Copy healthcheck script
COPY 02-data-processing/tick-aggregator/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Configure health check - verifies all dependencies
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=3 \
  CMD /app/healthcheck.sh

# Set Python path
ENV PYTHONPATH=/app

# Run aggregator
CMD ["python", "-u", "src/main.py"]
