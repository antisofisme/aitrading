# Use official Node.js runtime as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for security and performance
RUN apk add --no-cache \
    dumb-init \
    curl \
    && rm -rf /var/cache/apk/*

# Create non-root user for security (PCI DSS requirement)
RUN addgroup -g 1001 -S payment && \
    adduser -S payment -u 1001 -G payment

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY src/ ./src/
COPY .env.example .env

# Create logs directory
RUN mkdir -p logs && \
    chown -R payment:payment /app && \
    chmod -R 755 /app

# Switch to non-root user
USER payment

# Expose port
EXPOSE 3003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3003/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["node", "src/app.js"]

# Labels for metadata
LABEL maintainer="Neliti AI Trading Team"
LABEL version="1.0.0"
LABEL description="Unified payment service with Midtrans integration"
LABEL security.scan="required"
LABEL compliance="PCI-DSS"