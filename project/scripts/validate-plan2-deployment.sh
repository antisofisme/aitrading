#!/bin/bash

# AI Trading Platform - Plan2 Deployment Validation Script
# ========================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOCKER_COMPOSE_FILE="docker-compose-plan2.yml"
ENV_FILE=".env.plan2"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if deployment is running
check_deployment_status() {
    log "Checking deployment status..."

    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "Up"; then
        error "No services are running. Please start the deployment first."
        echo "Run: ./scripts/test-plan2-startup.sh"
        exit 1
    fi

    success "Deployment is active"
}

# Validate database connections
validate_databases() {
    log "Validating database connections..."

    local failed=0

    # PostgreSQL
    if docker exec ai-trading-postgres pg_isready -h localhost -p 5432 -U ai_trading_user &>/dev/null; then
        success "PostgreSQL connection"
    else
        error "PostgreSQL connection failed"
        ((failed++))
    fi

    # DragonflyDB
    if docker exec ai-trading-dragonflydb redis-cli ping &>/dev/null; then
        success "DragonflyDB connection"
    else
        error "DragonflyDB connection failed"
        ((failed++))
    fi

    # ClickHouse
    if docker exec ai-trading-clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping &>/dev/null; then
        success "ClickHouse connection"
    else
        error "ClickHouse connection failed"
        ((failed++))
    fi

    # Weaviate
    if docker exec ai-trading-weaviate curl -f http://localhost:8080/v1/.well-known/ready &>/dev/null; then
        success "Weaviate connection"
    else
        error "Weaviate connection failed"
        ((failed++))
    fi

    # ArangoDB
    if docker exec ai-trading-arangodb curl -f http://localhost:8529/_api/version &>/dev/null; then
        success "ArangoDB connection"
    else
        error "ArangoDB connection failed"
        ((failed++))
    fi

    # Redpanda
    if docker exec ai-trading-redpanda rpk cluster info &>/dev/null; then
        success "Redpanda connection"
    else
        error "Redpanda connection failed"
        ((failed++))
    fi

    if [ $failed -eq 0 ]; then
        success "All database connections validated"
    else
        error "$failed database connection(s) failed"
        return 1
    fi
}

# Validate core services
validate_core_services() {
    log "Validating core services..."

    local services=(
        "configuration-service:8012"
        "api-gateway:3001"
        "database-service:8008"
    )

    local failed=0

    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)

        if curl -f "http://localhost:$port/health" &>/dev/null; then
            success "$name health check"
        else
            error "$name health check failed"
            ((failed++))
        fi
    done

    if [ $failed -eq 0 ]; then
        success "All core services validated"
    else
        error "$failed core service(s) failed"
        return 1
    fi
}

# Validate trading services
validate_trading_services() {
    log "Validating trading services..."

    local services=(
        "ai-orchestrator:8020"
        "trading-engine:9000"
        "ml-predictor:8021"
        "risk-analyzer:8022"
        "portfolio-manager:9001"
        "order-management:9002"
    )

    local failed=0

    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)

        if curl -f "http://localhost:$port/health" &>/dev/null; then
            success "$name health check"
        else
            error "$name health check failed"
            ((failed++))
        fi
    done

    if [ $failed -eq 0 ]; then
        success "All trading services validated"
    else
        error "$failed trading service(s) failed"
        return 1
    fi
}

# Validate support services
validate_support_services() {
    log "Validating support services..."

    local services=(
        "data-bridge:5001"
        "central-hub:7000"
        "notification-service:9003"
        "user-management:8010"
        "billing-service:8011"
        "payment-service:8013"
    )

    local failed=0

    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)

        if curl -f "http://localhost:$port/health" &>/dev/null; then
            success "$name health check"
        else
            warning "$name health check failed (non-critical)"
        fi
    done

    success "Support services validation completed"
}

# Validate analytics services
validate_analytics_services() {
    log "Validating analytics services..."

    local services=(
        "performance-analytics:9100"
        "usage-monitoring:9101"
        "revenue-analytics:9102"
        "chain-debug-system:8030"
        "ai-chain-analytics:8031"
    )

    local failed=0

    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)

        if curl -f "http://localhost:$port/health" &>/dev/null; then
            success "$name health check"
        else
            warning "$name health check failed (non-critical)"
        fi
    done

    success "Analytics services validation completed"
}

# Test API functionality
test_api_functionality() {
    log "Testing API functionality..."

    # Test API Gateway
    if curl -s "http://localhost:3001/health" | jq -e '.status == "ok"' &>/dev/null; then
        success "API Gateway responds correctly"
    else
        error "API Gateway response invalid"
        return 1
    fi

    # Test Configuration Service
    if curl -s "http://localhost:8012/health" | jq -e '.status' &>/dev/null; then
        success "Configuration Service responds correctly"
    else
        error "Configuration Service response invalid"
        return 1
    fi

    # Test Database Service
    if curl -s "http://localhost:8008/health" &>/dev/null; then
        success "Database Service responds correctly"
    else
        error "Database Service response invalid"
        return 1
    fi

    success "API functionality tests passed"
}

# Check resource usage
check_resource_usage() {
    log "Checking resource usage..."

    # Memory usage
    local memory_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep -E "ai-trading-" | awk '{print $2}' | sed 's/MiB.*//' | awk '{sum+=$1} END {print sum}')

    if [ -n "$memory_usage" ]; then
        if [ "$memory_usage" -lt 8000 ]; then
            success "Memory usage: ${memory_usage}MB (Good)"
        elif [ "$memory_usage" -lt 12000 ]; then
            warning "Memory usage: ${memory_usage}MB (Moderate)"
        else
            warning "Memory usage: ${memory_usage}MB (High)"
        fi
    fi

    # Disk usage
    local disk_usage=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep -E "Images|Containers|Volumes" | awk '{print $2}' | sed 's/GB//' | awk '{sum+=$1} END {print sum}')

    if [ -n "$disk_usage" ]; then
        success "Disk usage: ${disk_usage}GB"
    fi
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."

    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$report_file" << EOF
AI Trading Platform - Plan2 Deployment Report
Generated: $(date)

=== CONTAINER STATUS ===
$(docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" ps --format table)

=== RESOURCE USAGE ===
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}")

=== NETWORK INFORMATION ===
$(docker network inspect ai-trading-network | jq '.[0].Containers')

=== SERVICE HEALTH ===
EOF

    # Append health check results
    for port in 3001 8012 8008 8020 9000 8021 8022; do
        local status="FAILED"
        if curl -f "http://localhost:$port/health" &>/dev/null; then
            status="OK"
        fi
        echo "Port $port: $status" >> "$report_file"
    done

    success "Report generated: $report_file"
}

# Main validation function
main() {
    log "Starting Plan2 Deployment Validation"
    echo "===================================="

    local validation_failed=0

    # Core validations (must pass)
    if ! check_deployment_status; then ((validation_failed++)); fi
    if ! validate_databases; then ((validation_failed++)); fi
    if ! validate_core_services; then ((validation_failed++)); fi
    if ! validate_trading_services; then ((validation_failed++)); fi
    if ! test_api_functionality; then ((validation_failed++)); fi

    # Optional validations (warnings only)
    validate_support_services
    validate_analytics_services

    # System checks
    check_resource_usage

    # Generate report
    generate_report

    echo ""
    if [ $validation_failed -eq 0 ]; then
        success "🎉 Plan2 deployment validation PASSED!"
        log "All critical services are running and responding correctly."

        echo ""
        log "Next steps:"
        echo "  1. Access API Gateway: http://localhost:3001"
        echo "  2. View Grafana dashboards: http://localhost:3000"
        echo "  3. Check Prometheus metrics: http://localhost:9090"
        echo "  4. Review the deployment report for detailed information"

        return 0
    else
        error "❌ Plan2 deployment validation FAILED!"
        log "$validation_failed critical validation(s) failed."
        echo ""
        log "Troubleshooting steps:"
        echo "  1. Check failed service logs: docker-compose logs [service-name]"
        echo "  2. Restart failed services: docker-compose restart [service-name]"
        echo "  3. Review the deployment report for detailed information"
        echo "  4. Check system resources and Docker daemon status"

        return 1
    fi
}

# Handle interrupts
trap 'error "Validation interrupted"; exit 1' INT TERM

# Run main function
main "$@"