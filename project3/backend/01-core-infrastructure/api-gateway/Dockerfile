# API Gateway - Suho Trading Platform
# Multi-stage build for production optimization

# Stage 1: Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy and install Central Hub SDK first
COPY 01-core-infrastructure/central-hub/sdk/nodejs /tmp/central-hub-sdk
WORKDIR /tmp/central-hub-sdk
RUN npm install && npm link

# Back to app directory
WORKDIR /app

# Copy package files
COPY 01-core-infrastructure/api-gateway/package*.json ./

# Link SDK and install dependencies
RUN npm link @suho/central-hub-sdk && \
    npm install --omit=dev && \
    npm cache clean --force

# Stage 2: Production stage
FROM node:18-alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S apigateway -u 1001

# Set working directory
WORKDIR /app

# Copy SDK node_modules from builder
COPY --from=builder --chown=apigateway:nodejs /usr/local/lib/node_modules/@suho /usr/local/lib/node_modules/@suho

# Copy dependencies from builder stage
COPY --from=builder --chown=apigateway:nodejs /app/node_modules ./node_modules

# Copy application source code
COPY --chown=apigateway:nodejs 01-core-infrastructure/api-gateway/ .

# Shared components already copied to build context

# Create logs directory
RUN mkdir -p logs && chown apigateway:nodejs logs

# Expose ports for API Gateway services
EXPOSE 8000 8001 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "const http = require('http'); \
    const options = { hostname: 'localhost', port: 8000, path: '/health', timeout: 5000 }; \
    const req = http.request(options, (res) => { \
        if (res.statusCode === 200) process.exit(0); \
        else process.exit(1); \
    }); \
    req.on('error', () => process.exit(1)); \
    req.on('timeout', () => { req.destroy(); process.exit(1); }); \
    req.end();"

# Switch to non-root user
USER apigateway

# Start API Gateway with dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "app.js"]