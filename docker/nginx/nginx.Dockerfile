# Nginx Dockerfile for Production SSL Termination
# Phase 1: High-Performance Reverse Proxy with Security

# Base stage with security hardening
FROM nginx:1.25-alpine AS base
LABEL maintainer="AI Trading Platform Team"
LABEL service="nginx-proxy"
LABEL version="1.0.0"
LABEL security="ssl-termination"

# Security: Install security updates and required packages
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        curl \
        openssl \
        certbot \
        certbot-nginx \
        tzdata && \
    rm -rf /var/cache/apk/*

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Security: Create non-root user for nginx worker processes
RUN addgroup -g 1001 -S aitrading && \
    adduser -S aitrading -u 1001 -G aitrading

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/cache/nginx /etc/nginx/ssl /etc/nginx/conf.d && \
    chown -R aitrading:aitrading /var/log/nginx /var/cache/nginx

# Security: Generate DH parameters for perfect forward secrecy
RUN openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048

# Copy custom nginx configuration
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/conf.d/ /etc/nginx/conf.d/
COPY docker/nginx/security/ /etc/nginx/security/

# Security: Set proper permissions
RUN chown -R root:root /etc/nginx && \
    chmod -R 644 /etc/nginx/conf.d/ && \
    chmod -R 644 /etc/nginx/security/ && \
    chmod 644 /etc/nginx/ssl/dhparam.pem

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose ports
EXPOSE 80 443

# Production stage
FROM base AS production

# Copy SSL certificate generation script
COPY docker/nginx/scripts/generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

# Copy entrypoint script
COPY docker/nginx/scripts/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Security and performance labels
LABEL security.scan="enabled"
LABEL security.updates="auto"
LABEL security.ssl="required"
LABEL security.headers="enabled"
LABEL performance.compression="enabled"
LABEL performance.caching="optimized"