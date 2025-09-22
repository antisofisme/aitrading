#!/bin/bash
# Development Deployment Script for AI Trading Platform
# Phase 1: Docker-based Development Environment Setup

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.dev"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.dev.yml"
MONITORING_COMPOSE="${PROJECT_ROOT}/docker/monitoring/docker-compose.monitoring.yml"

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

# Function to check prerequisites
check_prerequisites() {
    log_message "INFO" "Checking prerequisites for development deployment"

    # Check Docker
    if ! command -v docker > /dev/null 2>&1; then
        log_message "ERROR" "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose > /dev/null 2>&1; then
        log_message "ERROR" "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        log_message "ERROR" "Docker daemon is not running. Please start Docker first."
        exit 1
    fi

    # Check available disk space (minimum 10GB)
    local available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local min_space=10485760 # 10GB in KB

    if [[ "$available_space" -lt "$min_space" ]]; then
        log_message "WARN" "Low disk space detected. Minimum 10GB recommended."
    fi

    # Check available memory (minimum 4GB)
    local available_memory=$(free -k | awk 'NR==2{print $7}')
    local min_memory=4194304 # 4GB in KB

    if [[ "$available_memory" -lt "$min_memory" ]]; then
        log_message "WARN" "Low memory detected. Minimum 4GB recommended."
    fi

    log_message "SUCCESS" "Prerequisites check completed"
}

# Function to setup environment
setup_environment() {
    log_message "INFO" "Setting up development environment"

    # Copy environment file if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "${ENV_FILE}.example" ]]; then
            cp "${ENV_FILE}.example" "$ENV_FILE"
            log_message "INFO" "Created .env.dev from example file"
        else
            log_message "ERROR" "Environment example file not found: ${ENV_FILE}.example"
            exit 1
        fi
    fi

    # Generate random passwords if not set
    if ! grep -q "POSTGRES_PASSWORD=" "$ENV_FILE" || grep -q "POSTGRES_PASSWORD=$" "$ENV_FILE"; then
        local postgres_password=$(openssl rand -base64 32)
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$postgres_password/" "$ENV_FILE"
        log_message "INFO" "Generated PostgreSQL password"
    fi

    if ! grep -q "DRAGONFLY_PASSWORD=" "$ENV_FILE" || grep -q "DRAGONFLY_PASSWORD=$" "$ENV_FILE"; then
        local dragonfly_password=$(openssl rand -base64 32)
        sed -i "s/DRAGONFLY_PASSWORD=.*/DRAGONFLY_PASSWORD=$dragonfly_password/" "$ENV_FILE"
        log_message "INFO" "Generated DragonflyDB password"
    fi

    if ! grep -q "CLICKHOUSE_PASSWORD=" "$ENV_FILE" || grep -q "CLICKHOUSE_PASSWORD=$" "$ENV_FILE"; then
        local clickhouse_password=$(openssl rand -base64 32)
        sed -i "s/CLICKHOUSE_PASSWORD=.*/CLICKHOUSE_PASSWORD=$clickhouse_password/" "$ENV_FILE"
        log_message "INFO" "Generated ClickHouse password"
    fi

    if ! grep -q "JWT_SECRET_DEV=" "$ENV_FILE" || grep -q "JWT_SECRET_DEV=" "$ENV_FILE"; then
        local jwt_secret=$(openssl rand -base64 64)
        sed -i "s/JWT_SECRET_DEV=.*/JWT_SECRET_DEV=$jwt_secret/" "$ENV_FILE"
        log_message "INFO" "Generated JWT secret"
    fi

    # Set proper permissions
    chmod 600 "$ENV_FILE"

    log_message "SUCCESS" "Environment setup completed"
}

# Function to create directories
create_directories() {
    log_message "INFO" "Creating required directories"

    local directories=(
        "${PROJECT_ROOT}/logs"
        "${PROJECT_ROOT}/data/postgres"
        "${PROJECT_ROOT}/data/clickhouse"
        "${PROJECT_ROOT}/data/dragonfly"
        "${PROJECT_ROOT}/data/weaviate"
        "${PROJECT_ROOT}/data/arangodb"
        "${PROJECT_ROOT}/backup"
        "${PROJECT_ROOT}/temp"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_message "INFO" "Created directory: $dir"
        fi
    done

    # Set proper permissions
    chmod 755 "${PROJECT_ROOT}/logs"
    chmod 755 "${PROJECT_ROOT}/data"
    chmod 700 "${PROJECT_ROOT}/backup"

    log_message "SUCCESS" "Directories created successfully"
}

# Function to build images
build_images() {
    log_message "INFO" "Building Docker images"

    cd "$PROJECT_ROOT"

    # Pull base images first
    log_message "INFO" "Pulling base images"
    docker-compose -f "$COMPOSE_FILE" pull postgres-main clickhouse-logs dragonfly-cache weaviate arangodb

    # Build custom services
    log_message "INFO" "Building application services"
    docker-compose -f "$COMPOSE_FILE" build --parallel

    log_message "SUCCESS" "Docker images built successfully"
}

# Function to start services
start_services() {
    log_message "INFO" "Starting AI Trading Platform services"

    cd "$PROJECT_ROOT"

    # Start databases first
    log_message "INFO" "Starting database services"
    docker-compose -f "$COMPOSE_FILE" up -d postgres-main clickhouse-logs dragonfly-cache weaviate arangodb

    # Wait for databases to be ready
    log_message "INFO" "Waiting for databases to be ready"
    sleep 30

    # Start application services
    log_message "INFO" "Starting application services"
    docker-compose -f "$COMPOSE_FILE" up -d

    log_message "SUCCESS" "All services started successfully"
}

# Function to wait for services
wait_for_services() {
    log_message "INFO" "Waiting for services to be healthy"

    local max_attempts=60
    local attempt=0
    local services=(
        "aitrading-central-hub-dev"
        "aitrading-api-gateway-dev"
        "aitrading-database-service-dev"
        "aitrading-data-bridge-dev"
        "aitrading-trading-engine-dev"
    )

    while [[ $attempt -lt $max_attempts ]]; do
        local all_healthy=true

        for service in "${services[@]}"; do
            if ! docker ps --filter "name=$service" --filter "health=healthy" --format "table {{.Names}}" | grep -q "$service"; then
                all_healthy=false
                break
            fi
        done

        if [[ "$all_healthy" == "true" ]]; then
            log_message "SUCCESS" "All services are healthy"
            return 0
        fi

        log_message "INFO" "Waiting for services... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_message "WARN" "Some services may not be fully healthy yet"
    return 1
}

# Function to run health checks
run_health_checks() {
    log_message "INFO" "Running comprehensive health checks"

    if [[ -f "${PROJECT_ROOT}/docker/scripts/health-check.sh" ]]; then
        "${PROJECT_ROOT}/docker/scripts/health-check.sh" --timeout 15 --retry-count 2
    else
        log_message "WARN" "Health check script not found, skipping detailed checks"
    fi
}

# Function to setup monitoring (optional)
setup_monitoring() {
    if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
        log_message "INFO" "Setting up monitoring stack"

        if [[ -f "$MONITORING_COMPOSE" ]]; then
            docker-compose -f "$MONITORING_COMPOSE" up -d
            log_message "SUCCESS" "Monitoring stack started"
            log_message "INFO" "Grafana: http://localhost:3000 (admin/admin123)"
            log_message "INFO" "Prometheus: http://localhost:9090"
        else
            log_message "WARN" "Monitoring compose file not found"
        fi
    fi
}

# Function to display deployment summary
display_summary() {
    log_message "INFO" "=== DEPLOYMENT SUMMARY ==="
    echo ""
    echo "🎉 AI Trading Platform Development Environment is ready!"
    echo ""
    echo "Services:"
    echo "  📊 API Gateway:      http://localhost:8000"
    echo "  🏢 Central Hub:      http://localhost:8010"
    echo "  💾 Database Service: http://localhost:8008"
    echo "  🌉 Data Bridge:      http://localhost:8001 (WebSocket: ws://localhost:8001)"
    echo "  💹 Trading Engine:   http://localhost:8007"
    echo "  🔒 Security Monitor: http://localhost:8020"
    echo "  📝 Log Aggregator:   http://localhost:8030"
    echo ""
    echo "Databases:"
    echo "  🐘 PostgreSQL:       localhost:5432"
    echo "  📊 ClickHouse:       http://localhost:8123"
    echo "  🚀 DragonflyDB:      localhost:6379"
    echo "  🧠 Weaviate:         http://localhost:8080"
    echo "  🕸️  ArangoDB:         http://localhost:8529"
    echo ""
    if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
        echo "Monitoring:"
        echo "  📈 Grafana:          http://localhost:3000 (admin/admin123)"
        echo "  📊 Prometheus:       http://localhost:9090"
        echo "  🔍 Jaeger:           http://localhost:16686"
        echo ""
    fi
    echo "Useful commands:"
    echo "  📋 View logs:        docker-compose -f docker-compose.dev.yml logs -f [service]"
    echo "  🔍 Health check:     ./docker/scripts/health-check.sh"
    echo "  🛑 Stop services:    docker-compose -f docker-compose.dev.yml down"
    echo "  🗑️  Clean up:         docker-compose -f docker-compose.dev.yml down -v --remove-orphans"
    echo ""
    echo "Environment file: $ENV_FILE"
    echo "Compose file: $COMPOSE_FILE"
    echo ""
    echo "✅ Development deployment completed successfully!"
}

# Function to handle cleanup on exit
cleanup() {
    if [[ "${CLEANUP_ON_ERROR:-true}" == "true" ]]; then
        log_message "INFO" "Cleaning up on error"
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down > /dev/null 2>&1 || true
    fi
}

# Main execution
main() {
    echo -e "${BLUE}AI Trading Platform Development Deployment${NC}"
    echo -e "${BLUE}Phase 1: Docker-based Infrastructure Setup${NC}"
    echo ""

    # Set trap for cleanup
    trap cleanup ERR

    # Change to project root
    cd "$PROJECT_ROOT"

    # Run deployment steps
    check_prerequisites
    setup_environment
    create_directories
    build_images
    start_services
    wait_for_services
    run_health_checks
    setup_monitoring
    display_summary
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-monitoring)
            export ENABLE_MONITORING=true
            shift
            ;;
        --no-cleanup)
            export CLEANUP_ON_ERROR=false
            shift
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --with-monitoring     Enable monitoring stack (Grafana, Prometheus)"
            echo "  --no-cleanup          Don't cleanup on error"
            echo "  --env-file FILE       Use custom environment file"
            echo "  --compose-file FILE   Use custom compose file"
            echo "  --help                Show this help message"
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