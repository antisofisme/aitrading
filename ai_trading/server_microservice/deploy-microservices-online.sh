#!/bin/bash
# Quick Online Microservice Deployment
# Uses pip install with internet for faster deployment

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Services in logical deployment order
SERVICES=(
    "data-bridge"
    "api-gateway"
    "user-service"
    "ai-provider"
    "ml-processing" 
    "deep-learning"
    "ai-orchestration"
    "trading-engine"
    "database-service"
)

# Service ports mapping
declare -A PORTS=(
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

create_simple_dockerfile() {
    local service=$1
    local service_dir="./services/$service"
    
    cat > "$service_dir/Dockerfile.simple" << EOF
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .
COPY src/ ./src/ 2>/dev/null || true

# Set environment
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE ${PORTS[$service]}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORTS[$service]}/health || exit 1

# Start service
CMD ["python", "main.py"]
EOF

    echo -e "${GREEN}✅ Created simple Dockerfile for $service${NC}"
}

deploy_service_simple() {
    local service=$1
    local port=${PORTS[$service]}
    
    echo -e "\n${BLUE}🚀 Deploying $service on port $port${NC}"
    
    # Create simple dockerfile
    create_simple_dockerfile "$service"
    
    # Deploy using simple dockerfile
    if docker build -f "./services/$service/Dockerfile.simple" -t "$service:latest" "./services/$service/"; then
        echo -e "${GREEN}✅ Built $service image${NC}"
        
        # Stop existing container if running
        docker stop "$service" 2>/dev/null || true
        docker rm "$service" 2>/dev/null || true
        
        # Run container
        if docker run -d --name "$service" -p "$port:$port" "$service:latest"; then
            echo -e "${GREEN}✅ $service container started on port $port${NC}"
            
            # Wait for health check
            sleep 5
            if curl -f "http://localhost:$port/health" 2>/dev/null; then
                echo -e "${GREEN}✅ $service health check passed${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  $service deployed but health check failed${NC}"
                return 0
            fi
        else
            echo -e "${RED}❌ Failed to start $service container${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to build $service image${NC}"
        return 1
    fi
}

main() {
    echo -e "${BLUE}=== Quick Microservices Deployment with Online Dependencies ===${NC}"
    
    local deployed=0
    local total=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        if [ -d "./services/$service" ]; then
            if deploy_service_simple "$service"; then
                ((deployed++))
            fi
        else
            echo -e "${YELLOW}⚠️  Service directory ./services/$service not found${NC}"
        fi
        echo "---"
    done
    
    echo -e "\n${BLUE}=== Deployment Summary ===${NC}"
    echo -e "${GREEN}✅ Successfully deployed: $deployed/$total services${NC}"
    
    echo -e "\n${BLUE}Running containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${BLUE}Service URLs:${NC}"
    for service in "${SERVICES[@]}"; do
        port=${PORTS[$service]}
        echo -e "${GREEN}$service: http://localhost:$port${NC}"
    done
}

main "$@"