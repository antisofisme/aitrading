#!/bin/bash

# AI Trading Platform - Plan2 Docker Compose Startup Test Script
# =============================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose-plan2.yml"
ENV_FILE=".env.plan2"
TIMEOUT=300  # 5 minutes timeout for services to start
CHECK_INTERVAL=5  # Check every 5 seconds

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker-compose file exists
check_files() {
    log "Checking required files..."

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        error "Docker compose file $DOCKER_COMPOSE_FILE not found!"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file $ENV_FILE not found!"
        exit 1
    fi

    success "Required files found"
}

# Clean up previous containers
cleanup() {
    log "Cleaning up previous containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" down --volumes --remove-orphans || true
    success "Cleanup completed"
}

# Start core database services first
start_databases() {
    log "Starting database services..."

    # Start databases in order
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        postgres \
        dragonflydb \
        clickhouse \
        weaviate \
        arangodb \
        redpanda \
        redis

    success "Database services started"
}

# Wait for database health checks
wait_for_databases() {
    log "Waiting for databases to be healthy..."

    local databases=("postgres" "dragonflydb" "clickhouse" "weaviate" "arangodb" "redpanda" "redis")
    local start_time=$(date +%s)

    for db in "${databases[@]}"; do
        log "Waiting for $db to be healthy..."

        while true; do
            local current_time=$(date +%s)
            local elapsed=$((current_time - start_time))

            if [ $elapsed -gt $TIMEOUT ]; then
                error "Timeout waiting for $db to be healthy"
                return 1
            fi

            local health_status=$(docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" ps --format json | jq -r ".[] | select(.Service == \"$db\") | .Health")

            if [ "$health_status" == "healthy" ]; then
                success "$db is healthy"
                break
            elif [ "$health_status" == "unhealthy" ]; then
                error "$db is unhealthy"
                return 1
            else
                warning "$db health status: $health_status"
                sleep $CHECK_INTERVAL
            fi
        done
    done

    success "All databases are healthy"
}

# Test database connections
test_database_connections() {
    log "Testing database connections..."

    # Test PostgreSQL
    log "Testing PostgreSQL connection..."
    docker exec ai-trading-postgres pg_isready -h localhost -p 5432 -U ai_trading_user
    success "PostgreSQL connection successful"

    # Test DragonflyDB
    log "Testing DragonflyDB connection..."
    docker exec ai-trading-dragonflydb redis-cli ping
    success "DragonflyDB connection successful"

    # Test ClickHouse
    log "Testing ClickHouse connection..."
    docker exec ai-trading-clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping
    success "ClickHouse connection successful"

    # Test Weaviate
    log "Testing Weaviate connection..."
    docker exec ai-trading-weaviate curl -f http://localhost:8080/v1/.well-known/ready
    success "Weaviate connection successful"

    # Test ArangoDB
    log "Testing ArangoDB connection..."
    docker exec ai-trading-arangodb curl -f http://localhost:8529/_api/version
    success "ArangoDB connection successful"

    # Test Redpanda
    log "Testing Redpanda connection..."
    docker exec ai-trading-redpanda rpk cluster info
    success "Redpanda connection successful"

    success "All database connections successful"
}

# Start core services
start_core_services() {
    log "Starting core services..."

    # Start configuration service first
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d configuration-service

    # Wait for configuration service
    log "Waiting for configuration service..."
    local start_time=$(date +%s)

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -gt $TIMEOUT ]; then
            error "Timeout waiting for configuration service"
            return 1
        fi

        if curl -f http://localhost:8012/health &>/dev/null; then
            success "Configuration service is ready"
            break
        fi

        sleep $CHECK_INTERVAL
    done

    # Start API Gateway and Database Service
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        api-gateway \
        database-service

    success "Core services started"
}

# Wait for core services
wait_for_core_services() {
    log "Waiting for core services to be healthy..."

    local services=("configuration-service" "api-gateway" "database-service")
    local ports=("8012" "3001" "8008")

    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local port="${ports[$i]}"

        log "Waiting for $service on port $port..."

        local start_time=$(date +%s)
        while true; do
            local current_time=$(date +%s)
            local elapsed=$((current_time - start_time))

            if [ $elapsed -gt $TIMEOUT ]; then
                error "Timeout waiting for $service"
                return 1
            fi

            if curl -f "http://localhost:$port/health" &>/dev/null; then
                success "$service is ready"
                break
            fi

            sleep $CHECK_INTERVAL
        done
    done

    success "All core services are healthy"
}

# Start trading services
start_trading_services() {
    log "Starting trading services..."

    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        ai-orchestrator \
        trading-engine \
        ml-predictor \
        risk-analyzer \
        portfolio-manager \
        order-management

    success "Trading services started"
}

# Start support services
start_support_services() {
    log "Starting support services..."

    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        data-bridge \
        central-hub \
        notification-service \
        user-management \
        billing-service \
        payment-service \
        compliance-monitor \
        backtesting-engine

    success "Support services started"
}

# Start analytics services
start_analytics_services() {
    log "Starting analytics services..."

    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        performance-analytics \
        usage-monitoring \
        revenue-analytics \
        chain-debug-system \
        ai-chain-analytics

    success "Analytics services started"
}

# Start monitoring services
start_monitoring_services() {
    log "Starting monitoring services..."

    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d \
        prometheus \
        grafana \
        nginx

    success "Monitoring services started"
}

# Display service status
show_status() {
    log "Service Status Summary:"
    echo ""

    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" ps --format table

    echo ""
    log "Service URLs:"
    echo "🌐 API Gateway:           http://localhost:3001"
    echo "⚙️  Configuration Service: http://localhost:8012"
    echo "💾 Database Service:      http://localhost:8008"
    echo "🤖 AI Orchestrator:       http://localhost:8020"
    echo "📈 Trading Engine:        http://localhost:9000"
    echo "🧠 ML Predictor:          http://localhost:8021"
    echo "⚠️  Risk Analyzer:         http://localhost:8022"
    echo "📊 Performance Analytics: http://localhost:9100"
    echo "🔧 Chain Debug System:    http://localhost:8030"
    echo ""
    echo "📊 Monitoring:"
    echo "📈 Prometheus:            http://localhost:9090"
    echo "📊 Grafana:               http://localhost:3000"
    echo ""
    echo "💾 Databases:"
    echo "🐘 PostgreSQL:            localhost:5432"
    echo "🔥 DragonflyDB:           localhost:6379"
    echo "⚡ ClickHouse:            http://localhost:8123"
    echo "🔮 Weaviate:              http://localhost:8080"
    echo "🕸️  ArangoDB:              http://localhost:8529"
    echo "📡 Redpanda:              localhost:19092"
}

# Health check all services
health_check_all() {
    log "Performing comprehensive health check..."

    local failed_services=()

    # Check databases
    local databases=("postgres:5432" "dragonflydb:6379" "clickhouse:8123" "weaviate:8080" "arangodb:8529")
    for db in "${databases[@]}"; do
        local name=$(echo $db | cut -d: -f1)
        local port=$(echo $db | cut -d: -f2)

        if ! docker exec "ai-trading-$name" /bin/sh -c "exit 0" &>/dev/null; then
            failed_services+=("$name")
        fi
    done

    # Check application services
    local services=("3001" "8012" "8008" "8020" "9000" "8021" "8022" "9001" "9002")
    for port in "${services[@]}"; do
        if ! curl -f "http://localhost:$port/health" &>/dev/null; then
            failed_services+=("port-$port")
        fi
    done

    if [ ${#failed_services[@]} -eq 0 ]; then
        success "All services passed health check"
        return 0
    else
        error "Failed services: ${failed_services[*]}"
        return 1
    fi
}

# Main execution
main() {
    log "Starting AI Trading Platform Plan2 Deployment Test"
    echo "=================================================="

    # Phase 1: Preparation
    check_files
    cleanup

    # Phase 2: Database Layer
    start_databases
    wait_for_databases
    test_database_connections

    # Phase 3: Core Services
    start_core_services
    wait_for_core_services

    # Phase 4: Trading Services
    start_trading_services
    sleep 30  # Give services time to initialize

    # Phase 5: Support Services
    start_support_services
    sleep 20

    # Phase 6: Analytics Services
    start_analytics_services
    sleep 20

    # Phase 7: Monitoring Services
    start_monitoring_services
    sleep 10

    # Phase 8: Final Validation
    show_status

    if health_check_all; then
        success "🎉 Plan2 deployment test completed successfully!"
        log "All services are running and healthy."
        log "You can now access the services using the URLs listed above."
    else
        error "❌ Plan2 deployment test failed!"
        log "Some services are not responding. Check the logs for details."
        exit 1
    fi
}

# Handle interrupts
trap 'error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"