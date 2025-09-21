# Database Service Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    postgresql-client \
    curl \
    bash

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S dbservice -u 1001

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs && \
    mkdir -p migrations && \
    chown -R dbservice:nodejs /app

# Switch to non-root user
USER dbservice

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Start command
CMD ["npm", "start"]