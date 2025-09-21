#!/bin/sh
# Nginx entrypoint script for AI Trading Platform
# Phase 1: SSL certificate management and security initialization

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Nginx for AI Trading Platform${NC}"
echo -e "${BLUE}Phase 1: SSL Termination and Security Proxy${NC}"

# Default values
SSL_ENABLED=${SSL_ENABLED:-true}
DOMAIN_NAME=${DOMAIN_NAME:-localhost}
SSL_CERT_PATH="/etc/nginx/ssl/server.crt"
SSL_KEY_PATH="/etc/nginx/ssl/server.key"
DH_PARAM_PATH="/etc/nginx/ssl/dhparam.pem"

# Function to generate self-signed certificate
generate_self_signed_cert() {
    echo -e "${YELLOW}Generating self-signed SSL certificate for ${DOMAIN_NAME}${NC}"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_KEY_PATH" \
        -out "$SSL_CERT_PATH" \
        -subj "/C=US/ST=State/L=City/O=AI Trading Platform/OU=IT/CN=${DOMAIN_NAME}" \
        -addext "subjectAltName=DNS:${DOMAIN_NAME},DNS:*.${DOMAIN_NAME},DNS:localhost,IP:127.0.0.1"

    echo -e "${GREEN}Self-signed certificate generated successfully${NC}"
}

# Function to validate SSL certificate
validate_ssl_cert() {
    if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
        echo -e "${YELLOW}SSL certificate or key not found${NC}"
        return 1
    fi

    # Check if certificate is valid
    if ! openssl x509 -in "$SSL_CERT_PATH" -noout -checkend 86400; then
        echo -e "${YELLOW}SSL certificate is expired or will expire within 24 hours${NC}"
        return 1
    fi

    # Check if certificate and key match
    cert_modulus=$(openssl x509 -in "$SSL_CERT_PATH" -noout -modulus | md5sum)
    key_modulus=$(openssl rsa -in "$SSL_KEY_PATH" -noout -modulus 2>/dev/null | md5sum)

    if [ "$cert_modulus" != "$key_modulus" ]; then
        echo -e "${RED}SSL certificate and key do not match${NC}"
        return 1
    fi

    echo -e "${GREEN}SSL certificate validation passed${NC}"
    return 0
}

# Function to setup DH parameters
setup_dh_params() {
    if [ ! -f "$DH_PARAM_PATH" ]; then
        echo -e "${YELLOW}Generating DH parameters (this may take a while)...${NC}"
        openssl dhparam -out "$DH_PARAM_PATH" 2048
        echo -e "${GREEN}DH parameters generated successfully${NC}"
    else
        echo -e "${GREEN}DH parameters already exist${NC}"
    fi
}

# Function to setup security headers
setup_security_headers() {
    cat > /etc/nginx/security/headers.conf << 'EOF'
# Security headers for AI Trading Platform
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=(), vr=(), accelerometer=(), gyroscope=(), magnetometer=(), clipboard-read=(), clipboard-write=()" always;

# Remove server identification
more_clear_headers Server;
more_clear_headers X-Powered-By;
EOF

    echo -e "${GREEN}Security headers configured${NC}"
}

# Function to test nginx configuration
test_nginx_config() {
    echo -e "${BLUE}Testing Nginx configuration...${NC}"

    if nginx -t; then
        echo -e "${GREEN}Nginx configuration test passed${NC}"
        return 0
    else
        echo -e "${RED}Nginx configuration test failed${NC}"
        return 1
    fi
}

# Function to setup error pages
setup_error_pages() {
    mkdir -p /usr/share/nginx/html/error

    # Create custom error pages
    cat > /usr/share/nginx/html/error/404.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        .error { color: #333; }
    </style>
</head>
<body>
    <div class="error">
        <h1>404 - Page Not Found</h1>
        <p>The requested resource was not found on this server.</p>
    </div>
</body>
</html>
EOF

    cat > /usr/share/nginx/html/error/50x.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        .error { color: #333; }
    </style>
</head>
<body>
    <div class="error">
        <h1>Server Error</h1>
        <p>An internal server error occurred. Please try again later.</p>
    </div>
</body>
</html>
EOF

    cat > /usr/share/nginx/html/error/429.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>429 - Too Many Requests</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
        .error { color: #333; }
    </style>
</head>
<body>
    <div class="error">
        <h1>429 - Too Many Requests</h1>
        <p>Rate limit exceeded. Please wait before making more requests.</p>
    </div>
</body>
</html>
EOF

    echo -e "${GREEN}Error pages configured${NC}"
}

# Function to check backend services
check_backend_services() {
    echo -e "${BLUE}Checking backend services availability...${NC}"

    # Check API Gateway
    if timeout 5 nc -z api-gateway 8000; then
        echo -e "${GREEN}API Gateway is available${NC}"
    else
        echo -e "${YELLOW}API Gateway is not available yet${NC}"
    fi

    # Check Data Bridge
    if timeout 5 nc -z data-bridge 8001; then
        echo -e "${GREEN}Data Bridge is available${NC}"
    else
        echo -e "${YELLOW}Data Bridge is not available yet${NC}"
    fi

    # Check Security Monitor
    if timeout 5 nc -z security-monitor 8020; then
        echo -e "${GREEN}Security Monitor is available${NC}"
    else
        echo -e "${YELLOW}Security Monitor is not available yet${NC}"
    fi
}

# Main execution
echo -e "${BLUE}Setting up SSL and security configuration...${NC}"

# Create necessary directories
mkdir -p /etc/nginx/ssl /etc/nginx/security /var/log/nginx

# Setup security headers
setup_security_headers

# Setup error pages
setup_error_pages

# Setup DH parameters
if [ "$SSL_ENABLED" = "true" ]; then
    setup_dh_params

    # Validate or generate SSL certificate
    if ! validate_ssl_cert; then
        generate_self_signed_cert
    fi
fi

# Test nginx configuration
if ! test_nginx_config; then
    echo -e "${RED}Nginx configuration is invalid. Exiting.${NC}"
    exit 1
fi

# Check backend services (non-blocking)
check_backend_services

# Set proper permissions
chown -R nginx:nginx /var/log/nginx
chmod 644 /etc/nginx/ssl/*.crt 2>/dev/null || true
chmod 600 /etc/nginx/ssl/*.key 2>/dev/null || true
chmod 644 /etc/nginx/ssl/dhparam.pem 2>/dev/null || true

echo -e "${GREEN}Nginx setup completed successfully${NC}"
echo -e "${BLUE}Starting Nginx server...${NC}"

# Execute the main command
exec "$@"