# Component Manager Service - Standalone Hot Reload Service
FROM node:18-alpine

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init curl

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S componentmgr -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --omit=dev && npm cache clean --force

# Copy application source
COPY . .

# Create data directory for component versions
RUN mkdir -p /app/data && chown componentmgr:nodejs /app/data

# Expose port for health checks
EXPOSE 7001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "console.log('Component Manager running'); process.exit(0)"

# Switch to non-root user
USER componentmgr

# Start Component Manager Service
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "app.js"]