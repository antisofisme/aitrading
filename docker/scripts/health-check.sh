#!/bin/bash
# Health Check Script for AI Trading Platform Services
# Phase 1: Comprehensive Service Health Monitoring

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-/tmp/health-check.log}"
TIMEOUT="${TIMEOUT:-10}"
RETRY_COUNT="${RETRY_COUNT:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

# Service endpoints
declare -A SERVICES=(
    ["central-hub"]="http://localhost:8010/health"
    ["api-gateway"]="http://localhost:8000/health"
    ["database-service"]="http://localhost:8008/health"
    ["data-bridge"]="http://localhost:8001/health"
    ["trading-engine"]="http://localhost:8007/health"
    ["security-monitor"]="http://localhost:8020/health"
    ["log-aggregator"]="http://localhost:8030/health"
)

# Database endpoints
declare -A DATABASES=(
    ["postgres"]="postgres://aitrading:${POSTGRES_PASSWORD:-}@localhost:5432/aitrading_dev"
    ["clickhouse"]="http://localhost:8123/ping"
    ["dragonfly"]="redis://localhost:6379"
    ["weaviate"]="http://localhost:8080/v1/.well-known/ready"
    ["arangodb"]="http://localhost:8529/_api/version"
)

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    log_message "INFO" "Checking $name endpoint: $url"

    for attempt in $(seq 1 $RETRY_COUNT); do
        if response=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null); then
            status_code=$(echo "$response" | tail -n1)
            body=$(echo "$response" | head -n -1)

            if [[ "$status_code" == "$expected_status" ]]; then
                log_message "INFO" "✅ $name is healthy (Status: $status_code)"
                return 0
            else
                log_message "WARN" "⚠️  $name returned status $status_code (expected $expected_status)"
            fi
        else
            log_message "WARN" "❌ $name endpoint unreachable (attempt $attempt/$RETRY_COUNT)"
        fi

        if [[ $attempt -lt $RETRY_COUNT ]]; then
            sleep "$RETRY_DELAY"
        fi
    done

    log_message "ERROR" "❌ $name health check failed after $RETRY_COUNT attempts"
    return 1
}

# Function to check PostgreSQL
check_postgres() {
    local name="postgres"
    local connection_string="${DATABASES[$name]}"

    log_message "INFO" "Checking PostgreSQL database connection"

    for attempt in $(seq 1 $RETRY_COUNT); do
        if command -v pg_isready > /dev/null 2>&1; then
            if pg_isready -h localhost -p 5432 -U aitrading -d aitrading_dev > /dev/null 2>&1; then
                log_message "INFO" "✅ PostgreSQL is ready and accepting connections"
                return 0
            fi
        else
            # Fallback using psql
            if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U aitrading -d aitrading_dev -c "SELECT 1;" > /dev/null 2>&1; then
                log_message "INFO" "✅ PostgreSQL is ready and accepting connections"
                return 0
            fi
        fi

        log_message "WARN" "❌ PostgreSQL not ready (attempt $attempt/$RETRY_COUNT)"
        if [[ $attempt -lt $RETRY_COUNT ]]; then
            sleep "$RETRY_DELAY"
        fi
    done

    log_message "ERROR" "❌ PostgreSQL health check failed after $RETRY_COUNT attempts"
    return 1
}

# Function to check Redis/DragonflyDB
check_redis() {
    local name="dragonfly"

    log_message "INFO" "Checking DragonflyDB/Redis connection"

    for attempt in $(seq 1 $RETRY_COUNT); do
        if command -v redis-cli > /dev/null 2>&1; then
            if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
                log_message "INFO" "✅ DragonflyDB/Redis is responding to ping"
                return 0
            fi
        else
            # Fallback using nc
            if nc -z localhost 6379 > /dev/null 2>&1; then
                log_message "INFO" "✅ DragonflyDB/Redis port is open"
                return 0
            fi
        fi

        log_message "WARN" "❌ DragonflyDB/Redis not responding (attempt $attempt/$RETRY_COUNT)"
        if [[ $attempt -lt $RETRY_COUNT ]]; then
            sleep "$RETRY_DELAY"
        fi
    done

    log_message "ERROR" "❌ DragonflyDB/Redis health check failed after $RETRY_COUNT attempts"
    return 1
}

# Function to check container status
check_docker_containers() {
    log_message "INFO" "Checking Docker container status"

    local containers=(
        "aitrading-central-hub"
        "aitrading-api-gateway"
        "aitrading-database-service"
        "aitrading-data-bridge"
        "aitrading-trading-engine"
        "aitrading-postgres"
        "aitrading-clickhouse"
        "aitrading-dragonfly"
    )

    local all_healthy=true

    for container in "${containers[@]}"; do
        if docker ps --filter "name=${container}" --filter "status=running" --format "table {{.Names}}" | grep -q "$container"; then
            log_message "INFO" "✅ Container $container is running"
        else
            log_message "ERROR" "❌ Container $container is not running"
            all_healthy=false
        fi
    done

    if [[ "$all_healthy" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    log_message "INFO" "Checking disk space"

    local threshold=85
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ "$disk_usage" -lt "$threshold" ]]; then
        log_message "INFO" "✅ Disk space usage: ${disk_usage}% (threshold: ${threshold}%)"
        return 0
    else
        log_message "WARN" "⚠️  Disk space usage: ${disk_usage}% (threshold: ${threshold}%)"
        return 1
    fi
}

# Function to check memory usage
check_memory_usage() {
    log_message "INFO" "Checking memory usage"

    local threshold=85
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    if [[ "$memory_usage" -lt "$threshold" ]]; then
        log_message "INFO" "✅ Memory usage: ${memory_usage}% (threshold: ${threshold}%)"
        return 0
    else
        log_message "WARN" "⚠️  Memory usage: ${memory_usage}% (threshold: ${threshold}%)"
        return 1
    fi
}

# Function to check network connectivity
check_network() {
    log_message "INFO" "Checking network connectivity"

    local test_hosts=("8.8.8.8" "1.1.1.1")

    for host in "${test_hosts[@]}"; do
        if ping -c 1 -W 5 "$host" > /dev/null 2>&1; then
            log_message "INFO" "✅ Network connectivity to $host is working"
            return 0
        fi
    done

    log_message "WARN" "⚠️  Network connectivity issues detected"
    return 1
}

# Function to generate health report
generate_health_report() {
    local start_time="$1"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_message "INFO" "=== HEALTH CHECK REPORT ==="
    log_message "INFO" "Duration: ${duration}s"
    log_message "INFO" "Timestamp: $(date)"
    log_message "INFO" "Log file: $LOG_FILE"

    # Summary
    local total_checks=$((${#SERVICES[@]} + ${#DATABASES[@]} + 4)) # +4 for system checks
    local failed_checks=$(grep -c "❌" "$LOG_FILE" || echo "0")
    local success_rate=$(( (total_checks - failed_checks) * 100 / total_checks ))

    log_message "INFO" "Success rate: ${success_rate}%"
    log_message "INFO" "Failed checks: $failed_checks"

    if [[ "$failed_checks" -eq 0 ]]; then
        log_message "INFO" "🎉 All health checks passed!"
        return 0
    else
        log_message "ERROR" "💥 $failed_checks health check(s) failed"
        return 1
    fi
}

# Function to send alerts (placeholder)
send_alert() {
    local message="$1"
    local severity="${2:-warning}"

    # Placeholder for alerting system integration
    # This could be webhook, email, Slack, etc.
    log_message "ALERT" "[$severity] $message"

    # Example webhook call (uncomment and configure as needed)
    # if [[ -n "${WEBHOOK_URL:-}" ]]; then
    #     curl -X POST "$WEBHOOK_URL" \
    #         -H "Content-Type: application/json" \
    #         -d "{\"text\":\"[$severity] $message\",\"timestamp\":\"$(date -Iseconds)\"}" \
    #         > /dev/null 2>&1 || true
    # fi
}

# Main execution
main() {
    local start_time=$(date +%s)
    local overall_status=0

    echo -e "${BLUE}AI Trading Platform Health Check${NC}"
    echo -e "${BLUE}Phase 1: Infrastructure Health Monitoring${NC}"
    echo ""

    # Clear previous log
    > "$LOG_FILE"

    log_message "INFO" "Starting comprehensive health check"

    # Check system resources
    check_disk_space || overall_status=1
    check_memory_usage || overall_status=1
    check_network || overall_status=1

    # Check Docker containers
    if command -v docker > /dev/null 2>&1; then
        check_docker_containers || overall_status=1
    else
        log_message "WARN" "Docker not available, skipping container checks"
    fi

    # Check databases
    check_postgres || overall_status=1
    check_redis || overall_status=1

    # Check ClickHouse
    check_http_endpoint "ClickHouse" "${DATABASES[clickhouse]}" "200" || overall_status=1

    # Check Weaviate
    check_http_endpoint "Weaviate" "${DATABASES[weaviate]}" "200" || overall_status=1

    # Check ArangoDB
    check_http_endpoint "ArangoDB" "${DATABASES[arangodb]}" "200" || overall_status=1

    # Check application services
    for service in "${!SERVICES[@]}"; do
        check_http_endpoint "$service" "${SERVICES[$service]}" "200" || overall_status=1
    done

    # Generate report
    generate_health_report "$start_time" || overall_status=1

    # Send alerts if needed
    if [[ "$overall_status" -ne 0 ]]; then
        send_alert "AI Trading Platform health check failed. Check logs at $LOG_FILE" "critical"
    fi

    exit "$overall_status"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --retry-count)
            RETRY_COUNT="$2"
            shift 2
            ;;
        --retry-delay)
            RETRY_DELAY="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --timeout SECONDS      HTTP request timeout (default: 10)"
            echo "  --retry-count COUNT    Number of retries per check (default: 3)"
            echo "  --retry-delay SECONDS  Delay between retries (default: 5)"
            echo "  --log-file PATH        Log file path (default: /tmp/health-check.log)"
            echo "  --help                 Show this help message"
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