# AI Provider Service - Simplified for Fast Deployment
# Port: 8005, Expected Size: ~500MB dependencies

FROM python:3.11 as base

# Install system dependencies for AI Provider
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables optimized for AI Provider
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ================================================================
# DEPENDENCIES STAGE - OFFLINE WHEELS
# ================================================================
FROM base as dependencies

# Copy wheels for offline installation (90% faster deployment)
COPY wheels/ ./wheels/
COPY requirements.txt ./

# Install dependencies from offline wheels (no internet needed)
# Install wheels directly (ZERO internet access)
COPY install-wheels.sh ./
RUN chmod +x install-wheels.sh && ./install-wheels.sh && rm -rf wheels/ install-wheels.sh

# ================================================================
# APPLICATION STAGE
# ================================================================
FROM dependencies as application

# Copy AI Provider application code
COPY main.py .
COPY src/ ./src/
COPY config/ ./config/

# Create AI Provider specific directories
RUN mkdir -p /app/logs /app/cache /app/models /app/responses

# Set permissions
RUN chmod +x main.py

# ================================================================
# PRODUCTION STAGE
# ================================================================
FROM application as production

# AI Provider specific optimizations
ENV LLM_CACHE_SIZE=1000
ENV LLM_CACHE_TTL=1800
ENV MODEL_TIMEOUT=30
ENV RETRY_ATTEMPTS=3
ENV CONCURRENT_REQUESTS=10

# Model routing optimizations
ENV LOAD_BALANCING=true
ENV FALLBACK_MODELS=true
ENV COST_OPTIMIZATION=true

# Security: Non-root user
RUN useradd --create-home --shell /bin/bash aiprovider
RUN chown -R aiprovider:aiprovider /app
USER aiprovider

# Expose AI Provider port
EXPOSE 8005

# Health check for AI Provider
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Start AI Provider
CMD ["python", "main.py"]