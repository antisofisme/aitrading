# Central Hub - Optimized Dockerfile (NO DOWNLOADS)
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY base/ ./base/
COPY shared/ ./shared/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 7000

# Health check using python instead of curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7000/health')" || exit 1

# Set Python path and run application
ENV PYTHONPATH=/app/shared:/app/base
WORKDIR /app/base
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7000"]