# Multi-stage Dockerfile for Security Monitor Service
# Phase 1: Zero-Trust Security Monitoring and Threat Detection

# Base stage with security hardening
FROM node:18-alpine AS base
LABEL maintainer="AI Trading Platform Team"
LABEL service="security-monitor"
LABEL version="1.0.0"
LABEL security="zero-trust-monitor"

# Security: Create non-root user
RUN addgroup -g 1001 -S aitrading && \
    adduser -S aitrading -u 1001 -G aitrading

# Security: Install security updates and required packages
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        curl \
        tini \
        ca-certificates \
        openssl \
        docker-cli \
        tzdata && \
    rm -rf /var/cache/apk/*

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Dependencies stage
FROM base AS dependencies
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies with security audit
RUN npm ci --only=production --audit && \
    npm cache clean --force

# Development stage
FROM dependencies AS development
WORKDIR /app

# Install dev dependencies
RUN npm ci --audit

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Security: Set proper permissions
RUN chown -R aitrading:aitrading /app

# Switch to non-root user
USER aitrading

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

# Expose port
EXPOSE 8020

# Security: Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Development command with hot reload
CMD ["npm", "run", "dev:security-monitor"]

# Production build stage
FROM dependencies AS build
WORKDIR /app

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Build TypeScript
RUN npm run build:security-monitor && \
    npm prune --production

# Production stage
FROM base AS production
WORKDIR /app

# Copy built application
COPY --from=build --chown=aitrading:aitrading /app/dist ./dist
COPY --from=build --chown=aitrading:aitrading /app/node_modules ./node_modules
COPY --from=build --chown=aitrading:aitrading /app/package*.json ./
COPY --chown=aitrading:aitrading config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/temp /app/reports /app/alerts && \
    chown -R aitrading:aitrading /app

# Security: Switch to non-root user
USER aitrading

# Health check with security validation
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8020/health && \
        curl -f http://localhost:8020/security/monitor-status || exit 1

# Expose port
EXPOSE 8020

# Security: Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Production command
CMD ["node", "dist/services/security-monitor/server.js"]

# Security monitoring configurations
ENV NODE_OPTIONS="--max-old-space-size=512 --enable-source-maps"
ENV NODE_ENV=production
ENV SECURITY_SCAN_INTERVAL=60
ENV THREAT_DETECTION=enabled
ENV AUDIT_REAL_TIME=enabled
ENV ALERT_THRESHOLD=medium
ENV CONTAINER_MONITORING=enabled

# Security labels
LABEL security.scan="enabled"
LABEL security.updates="auto"
LABEL security.user="aitrading"
LABEL security.network="monitor"
LABEL security.docker="read-only"
LABEL security.alerts="real-time"