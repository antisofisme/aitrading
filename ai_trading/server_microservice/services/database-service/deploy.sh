#!/bin/bash

# Database Service Deployment Script
# Neliti Trading Platform - Microservice Architecture

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="database-service"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  NELITI DATABASE SERVICE DEPLOYMENT"
    echo "=================================================="
    echo "  Microservice: Database Service"
    echo "  Stack: PostgreSQL + ClickHouse + DragonflyDB"
    echo "         + Weaviate + ArangoDB"
    echo "  Architecture: Per-Service Centralization"
    echo "=================================================="
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running on Windows (WSL)
    if [[ -f /proc/version ]] && grep -q Microsoft /proc/version; then
        log_info "Detected WSL environment"
        DOCKER_HOST_PATH="/mnt/f/WINDSURF/neliti_code/server_microservice/services/database-service"
    else
        DOCKER_HOST_PATH="$(pwd)"
    fi
    
    log_success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating environment file..."
        cat > "$ENV_FILE" << EOF
# Database Service Environment Configuration
# Generated on $(date)

# Service Configuration
MICROSERVICE_ENVIRONMENT=development
DATABASE_SERVICE_PORT=8008
DATABASE_SERVICE_HOST=0.0.0.0
DATABASE_SERVICE_DEBUG=true

# PostgreSQL Configuration
POSTGRESQL_ENABLED=true
POSTGRESQL_HOST=postgresql
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=neliti_main
POSTGRESQL_USER=neliti_user
POSTGRESQL_PASSWORD=neliti_password_2024

# ClickHouse Configuration
CLICKHOUSE_ENABLED=true
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=trading_data
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=clickhouse_password_2024

# DragonflyDB Configuration
DRAGONFLYDB_ENABLED=true
DRAGONFLYDB_HOST=dragonflydb
DRAGONFLYDB_PORT=6379
DRAGONFLYDB_PASSWORD=dragonfly_password_2024

# Weaviate Configuration
WEAVIATE_ENABLED=true
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=weaviate_api_key_2024

# ArangoDB Configuration
ARANGODB_ENABLED=true
ARANGODB_HOST=arangodb
ARANGODB_PORT=8529
ARANGODB_DATABASE=neliti_graph
ARANGODB_USER=root
ARANGODB_PASSWORD=arangodb_password_2024

# Performance Settings
PERFORMANCE_QUERY_CACHE_ENABLED=true
PERFORMANCE_QUERY_CACHE_TTL_SECONDS=300
PERFORMANCE_BULK_INSERT_BATCH_SIZE=1000

# Monitoring
MONITORING_SLOW_QUERY_THRESHOLD_MS=1000
MONITORING_PERFORMANCE_LOGGING=true
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_QUERY_LOGGING=true
ENABLE_CONNECTION_LOGGING=true
EOF
        log_success "Environment file created: $ENV_FILE"
    else
        log_info "Environment file already exists: $ENV_FILE"
    fi
}

# Create directories
setup_directories() {
    log_info "Setting up data directories..."
    
    # Create data directories
    mkdir -p data/{postgresql,clickhouse,dragonflydb,weaviate,arangodb,arangodb-apps}
    mkdir -p logs/{database-service,clickhouse}
    
    # Set permissions (if not on Windows)
    if [[ ! -f /proc/version ]] || ! grep -q Microsoft /proc/version; then
        chmod 755 data/{postgresql,clickhouse,dragonflydb,weaviate,arangodb,arangodb-apps}
        chmod 755 logs/{database-service,clickhouse}
    fi
    
    log_success "Data directories created"
}

# Build services
build_services() {
    log_info "Building database service..."
    
    docker-compose build --no-cache database-service
    
    log_success "Database service built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying database stack..."
    
    # Pull images first
    log_info "Pulling database images..."
    docker-compose pull postgresql clickhouse dragonflydb weaviate arangodb
    
    # Start databases first
    log_info "Starting database containers..."
    docker-compose up -d postgresql clickhouse dragonflydb weaviate arangodb
    
    # Wait for databases to be ready
    log_info "Waiting for databases to initialize..."
    sleep 30
    
    # Check database health
    check_database_health
    
    # Start database service
    log_info "Starting database service..."
    docker-compose up -d database-service
    
    log_success "Database stack deployed successfully"
}

# Check database health
check_database_health() {
    log_info "Checking database health..."
    
    # PostgreSQL health check
    log_info "Checking PostgreSQL..."
    timeout 60s bash -c 'until docker-compose exec -T postgresql pg_isready -U neliti_user -d neliti_main; do sleep 2; done' || {
        log_warning "PostgreSQL health check timeout"
    }
    
    # ClickHouse health check
    log_info "Checking ClickHouse..."
    timeout 60s bash -c 'until docker-compose exec -T clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping; do sleep 2; done' || {
        log_warning "ClickHouse health check timeout"
    }
    
    # DragonflyDB health check
    log_info "Checking DragonflyDB..."
    timeout 60s bash -c 'until docker-compose exec -T dragonflydb redis-cli --no-auth-warning -a dragonfly_password_2024 ping; do sleep 2; done' || {
        log_warning "DragonflyDB health check timeout"
    }
    
    # Weaviate health check
    log_info "Checking Weaviate..."
    timeout 60s bash -c 'until docker-compose exec -T weaviate curl -f http://localhost:8080/v1/.well-known/ready; do sleep 2; done' || {
        log_warning "Weaviate health check timeout"
    }
    
    # ArangoDB health check
    log_info "Checking ArangoDB..."
    timeout 60s bash -c 'until docker-compose exec -T arangodb curl -f http://localhost:8529/_api/version; do sleep 2; done' || {
        log_warning "ArangoDB health check timeout"
    }
    
    log_success "Database health checks completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check running containers
    log_info "Checking running containers..."
    docker-compose ps
    
    # Check database service health
    log_info "Checking database service health..."
    sleep 10
    
    if curl -f http://localhost:8008/health > /dev/null 2>&1; then
        log_success "Database service is healthy"
    else
        log_warning "Database service health check failed"
    fi
    
    # Check service status
    if curl -f http://localhost:8008/status > /dev/null 2>&1; then
        log_success "Database service status endpoint is accessible"
    else
        log_warning "Database service status endpoint is not accessible"
    fi
}

# Show service information
show_service_info() {
    echo -e "${GREEN}"
    echo "=================================================="
    echo "  DATABASE SERVICE DEPLOYMENT COMPLETED"
    echo "=================================================="
    echo -e "${NC}"
    
    echo "🚀 Service Endpoints:"
    echo "   Database Service: http://localhost:8008"
    echo "   Health Check:     http://localhost:8008/health"
    echo "   Service Status:   http://localhost:8008/status"
    echo "   API Docs:         http://localhost:8008/docs"
    echo ""
    
    echo "💾 Database Endpoints:"
    echo "   PostgreSQL:   localhost:5432 (neliti_user/neliti_password_2024)"
    echo "   ClickHouse:   localhost:8123 (default/clickhouse_password_2024)"
    echo "   DragonflyDB:  localhost:6379 (dragonfly_password_2024)"
    echo "   Weaviate:     localhost:8080 (weaviate_api_key_2024)"
    echo "   ArangoDB:     localhost:8529 (root/arangodb_password_2024)"
    echo ""
    
    echo "📊 Management Commands:"
    echo "   View logs:        docker-compose logs -f database-service"
    echo "   View all logs:    docker-compose logs -f"
    echo "   Stop services:    docker-compose down"
    echo "   Restart service:  docker-compose restart database-service"
    echo "   Check status:     docker-compose ps"
    echo ""
    
    echo "🔧 Useful API Examples:"
    echo "   Test PostgreSQL: curl 'http://localhost:8008/api/v1/postgresql/query?query=SELECT version();'"
    echo "   Test ClickHouse:  curl 'http://localhost:8008/api/v1/clickhouse/query?query=SELECT version();'"
    echo "   Test Cache:       curl 'http://localhost:8008/api/v1/cache/get/test_key'"
    echo ""
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose down --remove-orphans
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            print_banner
            check_prerequisites
            setup_environment
            setup_directories
            build_services
            deploy_services
            verify_deployment
            show_service_info
            ;;
        "build")
            log_info "Building database service only..."
            build_services
            ;;
        "start")
            log_info "Starting database stack..."
            docker-compose up -d
            verify_deployment
            show_service_info
            ;;
        "stop")
            log_info "Stopping database stack..."
            docker-compose down
            log_success "Database stack stopped"
            ;;
        "restart")
            log_info "Restarting database stack..."
            docker-compose restart
            verify_deployment
            ;;
        "logs")
            docker-compose logs -f "${2:-database-service}"
            ;;
        "status")
            docker-compose ps
            curl -s http://localhost:8008/health | jq . 2>/dev/null || curl http://localhost:8008/health
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy    - Full deployment (default)"
            echo "  build     - Build database service only"
            echo "  start     - Start all services"
            echo "  stop      - Stop all services"
            echo "  restart   - Restart all services"
            echo "  logs      - Show logs (specify service name as 2nd arg)"
            echo "  status    - Show service status"
            echo "  cleanup   - Stop and remove all containers"
            echo "  help      - Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"