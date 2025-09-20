#!/bin/bash
# Microservice Individual Deployment Script
# Deploy each service independently with proper dependency management

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Services in dependency order
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

# Service ports
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

# Function to fix dockerfile requirements path
fix_dockerfile() {
    local service=$1
    local dockerfile_path="./services/$service/Dockerfile"
    
    if [ -f "$dockerfile_path" ]; then
        # Check if requirements/ directory exists
        if [ ! -d "./services/$service/requirements/" ]; then
            echo -e "${YELLOW}Fixing Dockerfile for $service - removing requirements/ directory reference${NC}"
            # Remove the COPY requirements/ line from Dockerfile
            sed -i '/COPY requirements\/ \.\/requirements\//d' "$dockerfile_path"
        fi
    fi
}

# Function to deploy a single service
deploy_service() {
    local service=$1
    local port=${SERVICE_PORTS[$service]}
    
    echo -e "\n${BLUE}🚀 Deploying Service: $service (Port: $port)${NC}"
    
    # Fix Dockerfile if needed
    fix_dockerfile "$service"
    
    # Build and deploy the service
    if docker-compose up -d --build "$service"; then
        echo -e "${GREEN}✅ Service $service deployed successfully${NC}"
        
        # Wait a moment for service to start
        sleep 3
        
        # Check if service is running
        if docker-compose ps "$service" | grep -q "running"; then
            echo -e "${GREEN}✅ Service $service is running on port $port${NC}"
            return 0
        else
            echo -e "${RED}❌ Service $service failed to start${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to deploy service $service${NC}"
        return 1
    fi
}

# Main deployment function
deploy_all_services() {
    echo -e "${BLUE}=== Starting Individual Microservice Deployment ===${NC}\n"
    
    local success_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        if deploy_service "$service"; then
            ((success_count++))
        else
            echo -e "${YELLOW}⚠️  Continuing with next service despite $service failure${NC}"
        fi
        echo "---"
    done
    
    echo -e "\n${BLUE}=== Deployment Summary ===${NC}"
    echo -e "${GREEN}✅ Successfully deployed: $success_count/$total_count services${NC}"
    
    # Show running services
    echo -e "\n${BLUE}Running Services:${NC}"
    docker-compose ps
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    deploy_all_services
fi