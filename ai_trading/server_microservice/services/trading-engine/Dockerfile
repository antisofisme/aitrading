# Trading Engine Service - Full Trading Capabilities
# Optimized for local wheels deployment with complete trading functionality  
# Port: 8007, TA-Lib, mathematical analysis, risk management

FROM python:3.11 as base

# Install system dependencies required for trading libraries
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables optimized for Trading Engine
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ================================================================
# DEPENDENCIES STAGE - Install Python packages
# ================================================================
FROM base as dependencies

# Copy wheels for offline installation
COPY wheels/ ./wheels/
COPY requirements.txt ./

# Install dependencies from local wheels (offline, fast)
COPY install-wheels.sh ./
RUN echo "🚀 Trading Engine: Installing dependencies from local wheels..." && \
    chmod +x install-wheels.sh && ./install-wheels.sh && rm -rf wheels/ install-wheels.sh

# ================================================================
# APPLICATION STAGE - Copy application code
# ================================================================
FROM dependencies as application

# Copy Trading Engine application code
COPY main.py .
COPY src/ ./src/

# Create Trading Engine specific directories
RUN mkdir -p /app/logs /app/cache /app/signals /app/strategies

# Set permissions
RUN chmod +x main.py

# ================================================================
# PRODUCTION OPTIMIZATION
# ================================================================
FROM application as production

# Trading Engine specific optimizations
ENV TRADING_CACHE_SIZE=1000
ENV SIGNAL_CACHE_TTL=300
ENV MAX_CONCURRENT_TRADES=5

# Security: Non-root user for trading
RUN groupadd -r trading && useradd --no-log-init -r -g trading trading
RUN chown -R trading:trading /app
USER trading

# Expose Trading Engine port
EXPOSE 8007

# Health check for Trading Engine
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Start Trading Engine
CMD ["python", "main.py"]