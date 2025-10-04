FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY sql/ ./sql/

# Create log directory
RUN mkdir -p /var/log/clickhouse-consumer

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the consumer
CMD ["python3", "src/main.py"]
