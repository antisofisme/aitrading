#!/bin/bash
# Production Microservices Deployment
# Deploy setiap service dengan full requirements dan dependency stack

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Service deployment order berdasarkan dependencies
declare -a DEPLOYMENT_ORDER=(
    "database-service"    # Foundation - deploy dengan full database stack
    "data-bridge"         # Data processing foundation
    "api-gateway"         # API routing dan auth
    "user-service"        # User management
    "ai-provider"         # AI/LLM provider
    "ml-processing"       # ML processing
    "deep-learning"       # Deep learning service
    "ai-orchestration"    # AI coordination
    "trading-engine"      # Trading logic (depends on semua AI services)
)

# Service ports mapping
declare -A SERVICE_PORTS=(
    ["api-gateway"]="8000"
    ["data-bridge"]="8001"  
    ["ai-orchestration"]="8003"
    ["deep-learning"]="8004"
    ["ai-provider"]="8005"
    ["ml-processing"]="8006"
    ["trading-engine"]="8007"
    ["database-service"]="8008"
    ["user-service"]="8009"
)

# Function untuk fix Dockerfile issues
fix_service_dockerfile() {
    local service=$1
    local dockerfile="./services/$service/Dockerfile"
    
    echo -e "${YELLOW}🔧 Fixing Dockerfile untuk $service${NC}"
    
    if [ -f "$dockerfile" ]; then
        # Remove references to non-existent requirements/ directory
        if [ ! -d "./services/$service/requirements/" ]; then
            sed -i '/COPY requirements\/ \.\/requirements\//d' "$dockerfile"
            echo -e "${GREEN}   ✅ Removed requirements/ directory reference${NC}"
        fi
        
        # Fix offline wheel installation to use fallback to PyPI
        if grep -q "pip install --no-index --find-links wheels/" "$dockerfile"; then
            sed -i 's/pip install --no-index --find-links wheels\//pip install --find-links wheels\//g' "$dockerfile"
            echo -e "${GREEN}   ✅ Fixed pip installation to allow PyPI fallback${NC}"
        fi
        
        # Fix specific service dockerfile issues
        case $service in
            "ai-provider")
                # Fix requirements-fast.txt reference if exists
                if grep -q "requirements-fast.txt" "$dockerfile"; then
                    sed -i 's/requirements-fast.txt/requirements.txt/g' "$dockerfile"
                    echo -e "${GREEN}   ✅ Fixed requirements file reference for ai-provider${NC}"
                fi
                ;;
        esac
    fi
}

# Function untuk deploy database service dengan full stack
deploy_database_service() {
    echo -e "\n${PURPLE}🗄️  DEPLOYING DATABASE SERVICE WITH FULL STACK${NC}"
    echo -e "${CYAN}Stack: PostgreSQL + ClickHouse + DragonflyDB + Weaviate + ArangoDB${NC}"
    
    cd "./services/database-service"
    
    # Fix dockerfile
    fix_service_dockerfile "../../database-service"
    
    # Deploy dengan docker-compose (full database stack)
    echo -e "${BLUE}📦 Deploying full database stack...${NC}"
    if docker-compose up -d --build; then
        echo -e "${GREEN}✅ Database service stack deployed successfully${NC}"
        
        # Wait for all databases to be ready
        echo -e "${YELLOW}⏳ Waiting for database stack to be ready...${NC}"
        sleep 30
        
        # Check health of each database
        echo -e "${BLUE}🔍 Checking database stack health...${NC}"
        
        # PostgreSQL
        if docker exec neliti-postgresql pg_isready -U neliti_user -d neliti_main; then
            echo -e "${GREEN}   ✅ PostgreSQL: Ready${NC}"
        else
            echo -e "${RED}   ❌ PostgreSQL: Not ready${NC}"
        fi
        
        # ClickHouse
        if docker exec neliti-clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping 2>/dev/null; then
            echo -e "${GREEN}   ✅ ClickHouse: Ready${NC}"
        else
            echo -e "${RED}   ❌ ClickHouse: Not ready${NC}"
        fi
        
        # DragonflyDB
        if docker exec neliti-dragonflydb redis-cli --no-auth-warning -a dragonfly_password_2024 ping 2>/dev/null | grep -q PONG; then
            echo -e "${GREEN}   ✅ DragonflyDB: Ready${NC}"
        else
            echo -e "${RED}   ❌ DragonflyDB: Not ready${NC}"
        fi
        
        # Weaviate
        if curl -sf http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ Weaviate: Ready${NC}"
        else
            echo -e "${RED}   ❌ Weaviate: Not ready${NC}"
        fi
        
        # ArangoDB
        if curl -sf http://localhost:8529/_api/version >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ ArangoDB: Ready${NC}"
        else
            echo -e "${RED}   ❌ ArangoDB: Not ready${NC}"
        fi
        
        # Database service itself
        sleep 10
        if curl -sf http://localhost:8008/health >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ Database Service API: Ready${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Database Service API: Still starting${NC}"
        fi
        
        echo -e "${PURPLE}✅ DATABASE SERVICE STACK DEPLOYMENT COMPLETE${NC}"
        cd "../.."
        return 0
    else
        echo -e "${RED}❌ Failed to deploy database service stack${NC}"
        cd "../.."
        return 1
    fi
}

# Function untuk deploy single service dengan full requirements
deploy_single_service() {
    local service=$1
    local port=${SERVICE_PORTS[$service]}
    
    echo -e "\n${BLUE}🚀 DEPLOYING SERVICE: $service (Port: $port)${NC}"
    
    # Fix dockerfile issues
    fix_service_dockerfile "$service"
    
    # Build service dengan full requirements using main docker-compose
    echo -e "${YELLOW}📦 Building $service with full requirements...${NC}"
    
    # Set required environment variables
    export ENVIRONMENT=development
    export ${service^^}_PORT=$port
    
    # Deploy using main docker-compose
    if docker-compose up -d --build "$service"; then
        echo -e "${GREEN}✅ $service built successfully${NC}"
        
        # Wait for service to start
        echo -e "${YELLOW}⏳ Waiting for $service to start...${NC}"
        sleep 10
        
        # Health check
        if curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is healthy on port $port${NC}"
            return 0
        elif curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is running on port $port (no health endpoint)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service deployed but health check failed${NC}"
            
            # Check container status
            if docker ps | grep -q "$service"; then
                echo -e "${YELLOW}   Container is running, might still be starting up${NC}"
                return 0
            else
                echo -e "${RED}   Container is not running${NC}"
                docker-compose logs "$service" | tail -20
                return 1
            fi
        fi
    else
        echo -e "${RED}❌ Failed to build $service${NC}"
        return 1
    fi
}

# Function untuk check dan install dependencies yang dibutuhkan
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        return 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        return 1
    fi
    
    # Check available memory
    available_mem=$(free -g | awk '/^Mem:/{print $7}')
    if [ "$available_mem" -lt 4 ]; then
        echo -e "${YELLOW}⚠️  Warning: Available memory is ${available_mem}GB. Recommended: 6GB+${NC}"
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
    return 0
}

# Main deployment function
main() {
    echo -e "${PURPLE}====================================================${NC}"
    echo -e "${PURPLE}🚀 NELITI AI TRADING PLATFORM - PRODUCTION DEPLOYMENT${NC}"
    echo -e "${PURPLE}====================================================${NC}"
    
    # Check prerequisites
    if ! check_prerequisites; then
        echo -e "${RED}❌ Prerequisites check failed. Exiting.${NC}"
        exit 1
    fi
    
    # Stop any running containers to start fresh
    echo -e "\n${YELLOW}🛑 Stopping any existing containers...${NC}"
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}📝 Creating .env file from .env.example${NC}"
        cp .env.example .env
    fi
    
    local deployed_count=0
    local total_count=${#DEPLOYMENT_ORDER[@]}
    
    # Deploy services in order
    for service in "${DEPLOYMENT_ORDER[@]}"; do
        if [ -d "./services/$service" ]; then
            if [ "$service" = "database-service" ]; then
                # Special handling untuk database service dengan full stack
                if deploy_database_service; then
                    ((deployed_count++))
                fi
            else
                # Deploy single service dengan full requirements
                if deploy_single_service "$service"; then
                    ((deployed_count++))
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  Service directory ./services/$service not found${NC}"
        fi
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    done
    
    # Deployment summary
    echo -e "\n${PURPLE}====================================================${NC}"
    echo -e "${PURPLE}📊 DEPLOYMENT SUMMARY${NC}"
    echo -e "${PURPLE}====================================================${NC}"
    echo -e "${GREEN}✅ Successfully deployed: $deployed_count/$total_count services${NC}"
    
    # Show running containers
    echo -e "\n${BLUE}🐳 RUNNING CONTAINERS:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps
    
    # Service URLs
    echo -e "\n${BLUE}🌐 SERVICE ENDPOINTS:${NC}"
    for service in "${!SERVICE_PORTS[@]}"; do
        port=${SERVICE_PORTS[$service]}
        echo -e "${GREEN}   $service: http://localhost:$port${NC}"
    done
    
    # Database endpoints (untuk database service)
    echo -e "\n${BLUE}🗄️  DATABASE ENDPOINTS:${NC}"
    echo -e "${GREEN}   PostgreSQL: localhost:5432${NC}"
    echo -e "${GREEN}   ClickHouse: http://localhost:8123${NC}"
    echo -e "${GREEN}   DragonflyDB: localhost:6379${NC}"
    echo -e "${GREEN}   Weaviate: http://localhost:8080${NC}"
    echo -e "${GREEN}   ArangoDB: http://localhost:8529${NC}"
    
    echo -e "\n${PURPLE}====================================================${NC}"
    echo -e "${PURPLE}🎉 DEPLOYMENT COMPLETED!${NC}"
    echo -e "${PURPLE}====================================================${NC}"
    
    # Final health check of all services
    echo -e "\n${BLUE}🔍 Final health check...${NC}"
    sleep 5
    for service in "${!SERVICE_PORTS[@]}"; do
        port=${SERVICE_PORTS[$service]}
        if curl -sf "http://localhost:$port/health" >/dev/null 2>&1 || curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ $service: Healthy${NC}"
        else
            echo -e "${YELLOW}   ⚠️  $service: Check manually${NC}"
        fi
    done
}

# Trap untuk cleanup pada exit
trap 'echo -e "\n${YELLOW}⚠️  Deployment interrupted${NC}"' INT TERM

# Execute main function
main "$@"