# Database Service Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p logs

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy source code
COPY src/ ./src/
COPY migrations/ ./migrations/

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S database-service -u 1001

# Change ownership of app directory
RUN chown -R database-service:nodejs /app

# Switch to non-root user
USER database-service

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8008/health || exit 1

# Start the service
CMD ["npm", "start"]