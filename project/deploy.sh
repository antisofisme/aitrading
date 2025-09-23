#!/bin/bash

# AI Trading Platform - Docker Deployment Script
# Enhanced with Flow-Aware Error Handling validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
LOG_FILE="deployment.log"
HEALTH_CHECK_TIMEOUT=300
VALIDATION_TIMEOUT=120

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        warning "Environment file not found: $ENV_FILE"
        log "Creating default environment file..."
        cp .env.example .env 2>/dev/null || true
    fi

    success "Prerequisites check completed"
}

# Build images
build_images() {
    log "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --parallel --no-cache
    success "Docker images built successfully"
}

# Start services
start_services() {
    log "Starting AI Trading Platform services..."

    # Start databases first
    log "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis clickhouse

    # Wait for databases to be ready
    wait_for_databases

    # Start core services
    log "Starting core services..."
    docker-compose -f "$COMPOSE_FILE" up -d configuration-service

    # Wait for configuration service (FlowRegistry)
    wait_for_service "configuration-service" 8012

    # Start remaining services
    log "Starting remaining services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    success "All services started"
}

# Wait for databases
wait_for_databases() {
    log "Waiting for databases to be ready..."

    # PostgreSQL
    log "Waiting for PostgreSQL..."
    timeout=60
    while ! docker exec ai-trading-postgres pg_isready -U ai_trading_user -d ai_trading >/dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "PostgreSQL failed to start within timeout"
            exit 1
        fi
    done
    success "PostgreSQL is ready"

    # Redis
    log "Waiting for Redis..."
    timeout=30
    while ! docker exec ai-trading-redis redis-cli ping >/dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "Redis failed to start within timeout"
            exit 1
        fi
    done
    success "Redis is ready"

    # ClickHouse
    log "Waiting for ClickHouse..."
    timeout=60
    while ! docker exec ai-trading-clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping >/dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "ClickHouse failed to start within timeout"
            exit 1
        fi
    done
    success "ClickHouse is ready"
}

# Wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    log "Waiting for $service_name on port $port..."

    timeout=120
    while ! curl -f "http://localhost:$port/health" >/dev/null 2>&1; do
        sleep 3
        timeout=$((timeout - 3))
        if [ $timeout -le 0 ]; then
            error "$service_name failed to start within timeout"
            return 1
        fi
    done
    success "$service_name is ready"
}

# Health check all services
health_check() {
    log "Performing comprehensive health checks..."

    # Service ports to check
    declare -A SERVICES=(
        ["api-gateway"]=3001
        ["data-bridge"]=5001
        ["central-hub"]=7000
        ["database-service"]=8008
        ["configuration-service"]=8012
        ["ai-orchestrator"]=8020
        ["ml-predictor"]=8021
        ["risk-analyzer"]=8022
        ["trading-engine"]=9000
        ["portfolio-manager"]=9001
        ["order-management"]=9002
        ["notification-service"]=9003
        ["performance-analytics"]=9100
        ["market-data-analyzer"]=9101
        ["reporting-service"]=9102
        ["chain-debug-system"]=8030
        ["ai-chain-analytics"]=8031
    )

    failed_services=()

    for service in "${!SERVICES[@]}"; do
        port=${SERVICES[$service]}
        log "Checking $service on port $port..."

        if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            success "$service is healthy"
        else
            error "$service health check failed"
            failed_services+=("$service")
        fi
    done

    if [ ${#failed_services[@]} -eq 0 ]; then
        success "All services are healthy!"
    else
        error "Failed services: ${failed_services[*]}"
        return 1
    fi
}

# Validate Flow-Aware Error Handling
validate_flow_system() {
    log "Validating Flow-Aware Error Handling system..."

    # Check FlowRegistry
    log "Testing FlowRegistry endpoints..."
    if curl -f "http://localhost:8012/api/flows" >/dev/null 2>&1; then
        success "FlowRegistry is responding"
    else
        error "FlowRegistry validation failed"
        return 1
    fi

    # Check Chain Debug System
    log "Testing Chain Debug System..."
    if curl -f "http://localhost:8030/api/chains/health" >/dev/null 2>&1; then
        success "Chain Debug System is responding"
    else
        error "Chain Debug System validation failed"
        return 1
    fi

    # Check AI Chain Analytics
    log "Testing AI Chain Analytics..."
    if curl -f "http://localhost:8031/api/analytics/status" >/dev/null 2>&1; then
        success "AI Chain Analytics is responding"
    else
        error "AI Chain Analytics validation failed"
        return 1
    fi

    success "Flow-Aware Error Handling system validation completed"
}

# Show service status
show_status() {
    log "Current service status:"
    docker-compose -f "$COMPOSE_FILE" ps

    log "\nService URLs:"
    echo "  API Gateway:           http://localhost:3001"
    echo "  Configuration Service: http://localhost:8012"
    echo "  Chain Debug System:    http://localhost:8030"
    echo "  AI Chain Analytics:    http://localhost:8031"
    echo "  Trading Engine:        http://localhost:9000"
    echo "  PostgreSQL:            localhost:5432"
    echo "  Redis:                 localhost:6379"
    echo "  ClickHouse:            localhost:8123"
}

# Stop services
stop_services() {
    log "Stopping AI Trading Platform services..."
    docker-compose -f "$COMPOSE_FILE" down
    success "Services stopped"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    docker system prune -f
    success "Cleanup completed"
}

# Main execution
case "${1:-up}" in
    "up")
        log "Starting AI Trading Platform deployment..."
        check_prerequisites
        build_images
        start_services
        health_check
        validate_flow_system
        show_status
        success "Deployment completed successfully!"
        ;;
    "down")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 5
        start_services
        health_check
        validate_flow_system
        show_status
        ;;
    "health")
        health_check
        validate_flow_system
        ;;
    "status")
        show_status
        ;;
    "logs")
        service=${2:-""}
        if [ -n "$service" ]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "clean")
        cleanup
        ;;
    "build")
        check_prerequisites
        build_images
        ;;
    *)
        echo "Usage: $0 {up|down|restart|health|status|logs [service]|clean|build}"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services with validation"
        echo "  down     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  health   - Check service health"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (optionally for specific service)"
        echo "  clean    - Clean up containers and volumes"
        echo "  build    - Build images only"
        exit 1
        ;;
esac