# Multi-stage Docker build for AI Trading Backend API
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY src/ ./src/

# Build TypeScript
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Create app user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S aitrading -u 1001

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder --chown=aitrading:nodejs /app/dist ./dist
COPY --from=builder --chown=aitrading:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=aitrading:nodejs /app/package*.json ./

# Create logs directory
RUN mkdir -p logs && chown -R aitrading:nodejs logs

# Install security updates
RUN apk update && apk upgrade && \
    apk add --no-cache dumb-init && \
    rm -rf /var/cache/apk/*

# Switch to non-root user
USER aitrading

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8000/health', (res) => process.exit(res.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["node", "dist/server.js"]