# Feature Engineering Service
FROM python:3.11-slim

WORKDIR /app

# No system dependencies needed - using pandas/numpy only

# Copy and install Central Hub SDK first (for ProgressLogger)
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Copy requirements
COPY 03-machine-learning/feature-engineering-service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY 03-machine-learning/feature-engineering-service/src/ ./src/
COPY 03-machine-learning/feature-engineering-service/config/ ./config/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME="feature-engineering-service"
ENV SERVICE_TYPE="ml-feature-engineering"
ENV SERVICE_VERSION="1.0.0"

# Run service
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main"]
