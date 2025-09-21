# Multi-stage Dockerfile for Trading Engine Service
# Phase 1: Server-Side Trading Authority with Audit Trail

# Base stage with security hardening
FROM node:18-alpine AS base
LABEL maintainer="AI Trading Platform Team"
LABEL service="trading-engine"
LABEL version="1.0.0"
LABEL security="server-side-authority"

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
    CMD curl -f http://localhost:8007/health || exit 1

# Expose port
EXPOSE 8007

# Security: Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Development command with hot reload
CMD ["npm", "run", "dev:trading-engine"]

# Production build stage
FROM dependencies AS build
WORKDIR /app

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Build TypeScript
RUN npm run build:trading-engine && \
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
RUN mkdir -p /app/logs /app/temp /app/audit /app/risk-models && \
    chown -R aitrading:aitrading /app

# Security: Switch to non-root user
USER aitrading

# Health check with trading engine validation
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8007/health && \
        curl -f http://localhost:8007/engine/status || exit 1

# Expose port
EXPOSE 8007

# Security: Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Production command
CMD ["node", "dist/services/trading-engine/server.js"]

# Trading engine configurations
ENV NODE_OPTIONS="--max-old-space-size=1024 --enable-source-maps"
ENV NODE_ENV=production
ENV TRADING_AUTHORITY=server-side
ENV RISK_MANAGEMENT=strict
ENV AUDIT_TRAIL=comprehensive
ENV SIGNAL_VALIDATION=enabled
ENV POSITION_LIMITS=enabled

# Security labels
LABEL security.scan="enabled"
LABEL security.updates="auto"
LABEL security.user="aitrading"
LABEL security.network="trading"
LABEL security.authority="server-only"
LABEL security.audit="comprehensive"
LABEL performance.latency="sub-50ms"