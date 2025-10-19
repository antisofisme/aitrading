FROM python:3.11-slim

WORKDIR /app

# Install central-hub SDK
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk/

# Install Python dependencies
COPY 02-data-processing/fe-service-temp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY 02-data-processing/fe-service-temp/src/ ./src/
COPY 02-data-processing/fe-service-temp/config/ ./config/

# Set environment
ENV PYTHONUNBUFFERED=1

# Run the service
CMD ["python", "-u", "src/main.py"]
