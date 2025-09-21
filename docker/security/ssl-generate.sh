#!/bin/bash
# SSL Certificate Generation Script for AI Trading Platform
# Phase 1: Security-First SSL/TLS Certificate Management

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}"
CONFIG_FILE="${SSL_DIR}/openssl.conf"
DOMAIN_NAME="${DOMAIN_NAME:-aitrading.local}"
ORG_NAME="${ORG_NAME:-AI Trading Platform}"
COUNTRY="${COUNTRY:-US}"
STATE="${STATE:-California}"
CITY="${CITY:-San Francisco}"

# Certificate files
CA_KEY="${SSL_DIR}/ca.key"
CA_CERT="${SSL_DIR}/ca.crt"
SERVER_KEY="${SSL_DIR}/server.key"
SERVER_CSR="${SSL_DIR}/server.csr"
SERVER_CERT="${SSL_DIR}/server.crt"
CLIENT_KEY="${SSL_DIR}/client.key"
CLIENT_CSR="${SSL_DIR}/client.csr"
CLIENT_CERT="${SSL_DIR}/client.crt"
DH_PARAM="${SSL_DIR}/dhparam.pem"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO")
            echo -e "${timestamp} ${BLUE}[INFO]${NC} ${message}"
            ;;
        "WARN")
            echo -e "${timestamp} ${YELLOW}[WARN]${NC} ${message}"
            ;;
        "ERROR")
            echo -e "${timestamp} ${RED}[ERROR]${NC} ${message}"
            ;;
        "SUCCESS")
            echo -e "${timestamp} ${GREEN}[SUCCESS]${NC} ${message}"
            ;;
    esac
}

# Function to create OpenSSL configuration
create_openssl_config() {
    log_message "INFO" "Creating OpenSSL configuration file"

    cat > "$CONFIG_FILE" << EOF
# OpenSSL Configuration for AI Trading Platform
# Generated on $(date)

[ req ]
default_bits = 4096
prompt = no
distinguished_name = req_distinguished_name
req_extensions = v3_req

[ req_distinguished_name ]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORG_NAME
OU = IT Department
CN = $DOMAIN_NAME

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical,CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[ v3_server ]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ v3_client ]
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection

[ alt_names ]
DNS.1 = $DOMAIN_NAME
DNS.2 = *.$DOMAIN_NAME
DNS.3 = localhost
DNS.4 = *.localhost
DNS.5 = api-gateway
DNS.6 = data-bridge
DNS.7 = central-hub
DNS.8 = database-service
DNS.9 = trading-engine
DNS.10 = security-monitor
DNS.11 = log-aggregator
IP.1 = 127.0.0.1
IP.2 = ::1
IP.3 = 172.20.0.1
IP.4 = 172.21.0.1
EOF

    log_message "SUCCESS" "OpenSSL configuration created: $CONFIG_FILE"
}

# Function to generate CA certificate
generate_ca_certificate() {
    log_message "INFO" "Generating Certificate Authority (CA)"

    # Generate CA private key
    openssl genpkey -algorithm RSA -out "$CA_KEY" -pkcs8 -aes256 -pass pass:aitrading-ca-2024
    chmod 600 "$CA_KEY"

    # Generate CA certificate
    openssl req -new -x509 -days 3650 -key "$CA_KEY" -out "$CA_CERT" \
        -config "$CONFIG_FILE" \
        -extensions v3_ca \
        -passin pass:aitrading-ca-2024 \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG_NAME/OU=Certificate Authority/CN=$ORG_NAME Root CA"

    chmod 644 "$CA_CERT"

    log_message "SUCCESS" "CA certificate generated: $CA_CERT"
    log_message "INFO" "CA certificate details:"
    openssl x509 -in "$CA_CERT" -text -noout | grep -E "(Subject:|Issuer:|Validity)"
}

# Function to generate server certificate
generate_server_certificate() {
    log_message "INFO" "Generating server certificate for $DOMAIN_NAME"

    # Generate server private key
    openssl genpkey -algorithm RSA -out "$SERVER_KEY" -pkcs8 -aes256 -pass pass:aitrading-server-2024
    chmod 600 "$SERVER_KEY"

    # Generate server certificate signing request
    openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" \
        -config "$CONFIG_FILE" \
        -passin pass:aitrading-server-2024

    # Generate server certificate signed by CA
    openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" \
        -CAcreateserial -out "$SERVER_CERT" -days 365 \
        -extensions v3_server -extfile "$CONFIG_FILE" \
        -passin pass:aitrading-ca-2024

    chmod 644 "$SERVER_CERT"

    # Remove CSR file
    rm -f "$SERVER_CSR"

    log_message "SUCCESS" "Server certificate generated: $SERVER_CERT"
    log_message "INFO" "Server certificate details:"
    openssl x509 -in "$SERVER_CERT" -text -noout | grep -E "(Subject:|Issuer:|Validity|DNS:|IP Address:)"
}

# Function to generate client certificate
generate_client_certificate() {
    log_message "INFO" "Generating client certificate for mutual TLS"

    # Generate client private key
    openssl genpkey -algorithm RSA -out "$CLIENT_KEY" -pkcs8 -aes256 -pass pass:aitrading-client-2024
    chmod 600 "$CLIENT_KEY"

    # Generate client certificate signing request
    openssl req -new -key "$CLIENT_KEY" -out "$CLIENT_CSR" \
        -config "$CONFIG_FILE" \
        -passin pass:aitrading-client-2024 \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG_NAME/OU=Client/CN=AI Trading Platform Client"

    # Generate client certificate signed by CA
    openssl x509 -req -in "$CLIENT_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" \
        -CAcreateserial -out "$CLIENT_CERT" -days 365 \
        -extensions v3_client -extfile "$CONFIG_FILE" \
        -passin pass:aitrading-ca-2024

    chmod 644 "$CLIENT_CERT"

    # Remove CSR file
    rm -f "$CLIENT_CSR"

    log_message "SUCCESS" "Client certificate generated: $CLIENT_CERT"
}

# Function to generate DH parameters
generate_dh_parameters() {
    log_message "INFO" "Generating Diffie-Hellman parameters (this may take a while)"

    openssl dhparam -out "$DH_PARAM" 2048
    chmod 644 "$DH_PARAM"

    log_message "SUCCESS" "DH parameters generated: $DH_PARAM"
}

# Function to create unencrypted versions for Docker
create_unencrypted_keys() {
    log_message "INFO" "Creating unencrypted key versions for Docker containers"

    # Create unencrypted server key
    openssl rsa -in "$SERVER_KEY" -out "${SERVER_KEY%.key}-unencrypted.key" \
        -passin pass:aitrading-server-2024
    chmod 600 "${SERVER_KEY%.key}-unencrypted.key"

    # Create unencrypted client key
    openssl rsa -in "$CLIENT_KEY" -out "${CLIENT_KEY%.key}-unencrypted.key" \
        -passin pass:aitrading-client-2024
    chmod 600 "${CLIENT_KEY%.key}-unencrypted.key"

    log_message "SUCCESS" "Unencrypted keys created for container use"
}

# Function to verify certificates
verify_certificates() {
    log_message "INFO" "Verifying certificate chain"

    # Verify server certificate against CA
    if openssl verify -CAfile "$CA_CERT" "$SERVER_CERT" > /dev/null 2>&1; then
        log_message "SUCCESS" "Server certificate verification passed"
    else
        log_message "ERROR" "Server certificate verification failed"
        return 1
    fi

    # Verify client certificate against CA
    if openssl verify -CAfile "$CA_CERT" "$CLIENT_CERT" > /dev/null 2>&1; then
        log_message "SUCCESS" "Client certificate verification passed"
    else
        log_message "ERROR" "Client certificate verification failed"
        return 1
    fi

    # Check certificate dates
    log_message "INFO" "Certificate validity periods:"
    echo "CA Certificate:"
    openssl x509 -in "$CA_CERT" -dates -noout
    echo "Server Certificate:"
    openssl x509 -in "$SERVER_CERT" -dates -noout
    echo "Client Certificate:"
    openssl x509 -in "$CLIENT_CERT" -dates -noout
}

# Function to create certificate bundle
create_certificate_bundle() {
    log_message "INFO" "Creating certificate bundles"

    # Create full chain for server
    cat "$SERVER_CERT" "$CA_CERT" > "${SSL_DIR}/server-fullchain.crt"

    # Create PKCS#12 bundle for easy import
    openssl pkcs12 -export -out "${SSL_DIR}/server.p12" \
        -inkey "${SERVER_KEY%.key}-unencrypted.key" \
        -in "$SERVER_CERT" \
        -certfile "$CA_CERT" \
        -passout pass:aitrading-p12-2024

    # Create client PKCS#12 bundle
    openssl pkcs12 -export -out "${SSL_DIR}/client.p12" \
        -inkey "${CLIENT_KEY%.key}-unencrypted.key" \
        -in "$CLIENT_CERT" \
        -certfile "$CA_CERT" \
        -passout pass:aitrading-client-p12-2024

    log_message "SUCCESS" "Certificate bundles created"
}

# Function to set proper permissions
set_permissions() {
    log_message "INFO" "Setting proper file permissions"

    # CA files
    chmod 600 "$CA_KEY"
    chmod 644 "$CA_CERT"

    # Server files
    chmod 600 "$SERVER_KEY"
    chmod 600 "${SERVER_KEY%.key}-unencrypted.key"
    chmod 644 "$SERVER_CERT"
    chmod 644 "${SSL_DIR}/server-fullchain.crt"

    # Client files
    chmod 600 "$CLIENT_KEY"
    chmod 600 "${CLIENT_KEY%.key}-unencrypted.key"
    chmod 644 "$CLIENT_CERT"

    # DH parameters
    chmod 644 "$DH_PARAM"

    # PKCS#12 files
    chmod 600 "${SSL_DIR}/server.p12"
    chmod 600 "${SSL_DIR}/client.p12"

    log_message "SUCCESS" "File permissions set correctly"
}

# Function to generate summary
generate_summary() {
    log_message "INFO" "SSL Certificate Generation Summary"
    echo ""
    echo "Generated files:"
    echo "  CA Certificate: $CA_CERT"
    echo "  CA Private Key: $CA_KEY (encrypted)"
    echo "  Server Certificate: $SERVER_CERT"
    echo "  Server Private Key: $SERVER_KEY (encrypted)"
    echo "  Server Private Key: ${SERVER_KEY%.key}-unencrypted.key (unencrypted for Docker)"
    echo "  Server Full Chain: ${SSL_DIR}/server-fullchain.crt"
    echo "  Client Certificate: $CLIENT_CERT"
    echo "  Client Private Key: $CLIENT_KEY (encrypted)"
    echo "  Client Private Key: ${CLIENT_KEY%.key}-unencrypted.key (unencrypted for Docker)"
    echo "  DH Parameters: $DH_PARAM"
    echo "  Server PKCS#12: ${SSL_DIR}/server.p12"
    echo "  Client PKCS#12: ${SSL_DIR}/client.p12"
    echo ""
    echo "Passwords:"
    echo "  CA Key: aitrading-ca-2024"
    echo "  Server Key: aitrading-server-2024"
    echo "  Client Key: aitrading-client-2024"
    echo "  Server P12: aitrading-p12-2024"
    echo "  Client P12: aitrading-client-p12-2024"
    echo ""
    echo "Domain: $DOMAIN_NAME"
    echo "Organization: $ORG_NAME"
    echo "Certificate validity: 1 year (server/client), 10 years (CA)"
}

# Main execution
main() {
    echo -e "${BLUE}AI Trading Platform SSL Certificate Generator${NC}"
    echo -e "${BLUE}Phase 1: Security-First Certificate Management${NC}"
    echo ""

    # Create SSL directory if it doesn't exist
    mkdir -p "$SSL_DIR"

    # Check if certificates already exist
    if [[ -f "$SERVER_CERT" ]] && [[ -f "$CA_CERT" ]]; then
        log_message "WARN" "Certificates already exist!"
        read -p "Do you want to regenerate them? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_message "INFO" "Keeping existing certificates"
            exit 0
        fi
    fi

    # Generate all certificates and keys
    create_openssl_config
    generate_ca_certificate
    generate_server_certificate
    generate_client_certificate
    generate_dh_parameters
    create_unencrypted_keys
    create_certificate_bundle
    verify_certificates
    set_permissions

    generate_summary

    log_message "SUCCESS" "SSL certificate generation completed successfully!"
    log_message "INFO" "You can now start the AI Trading Platform with SSL/TLS enabled"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --org)
            ORG_NAME="$2"
            shift 2
            ;;
        --country)
            COUNTRY="$2"
            shift 2
            ;;
        --state)
            STATE="$2"
            shift 2
            ;;
        --city)
            CITY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --domain DOMAIN    Domain name for certificate (default: aitrading.local)"
            echo "  --org ORG          Organization name (default: AI Trading Platform)"
            echo "  --country COUNTRY  Country code (default: US)"
            echo "  --state STATE      State name (default: California)"
            echo "  --city CITY        City name (default: San Francisco)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"