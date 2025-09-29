# Central Hub - Full Implementation Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY service/ ./service/
COPY shared/ ./shared/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 7000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7000/health || exit 1

# Set Python path and run application
ENV PYTHONPATH=/app/shared:/app/service
WORKDIR /app/service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7000"]