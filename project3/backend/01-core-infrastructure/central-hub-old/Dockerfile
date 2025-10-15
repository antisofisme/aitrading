# Central Hub - Optimized Dockerfile with Layer Caching
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching (this layer only rebuilds if requirements.txt changes)
COPY 01-core-infrastructure/central-hub/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY 01-core-infrastructure/central-hub/base/ ./base/
COPY 01-core-infrastructure/central-hub/shared/ ./shared/

# Create logs directory
RUN mkdir -p /app/logs

# Copy healthcheck script
COPY 01-core-infrastructure/central-hub/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Expose port
EXPOSE 7000

# Health check - verifies API responds
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD /app/healthcheck.sh

# Set Python path and run application
ENV PYTHONPATH=/app/shared:/app/base
WORKDIR /app/base
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7000"]