# Performance Analytics Service - Full Service
# Optimized for complete performance analytics with local wheels
# Port: 8010

FROM python:3.11

# Install system dependencies for analytics and financial calculations
RUN apt-get update && apt-get install -y \
    curl \
    gcc g++ \
    make \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy wheels for offline installation
COPY wheels/ ./wheels/
COPY requirements.txt ./
COPY install-wheels.sh ./

# Install dependencies using optimized wheels script  
RUN chmod +x install-wheels.sh && ./install-wheels.sh && rm -rf wheels/ install-wheels.sh

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/reports /app/data /app/logs /app/exports

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Start the service
CMD ["python", "main.py"]