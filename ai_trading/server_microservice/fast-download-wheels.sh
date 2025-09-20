#!/bin/bash
# Fast parallel download of wheels untuk semua services

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

download_service_wheels_fast() {
    local service=$1
    local service_dir="./services/$service"
    
    if [ ! -f "$service_dir/requirements.txt" ]; then
        echo -e "${YELLOW}⚠️  $service: No requirements.txt${NC}"
        return 1
    fi
    
    # Create wheels directory
    mkdir -p "$service_dir/wheels"
    
    # Download wheels quickly
    cd "$service_dir"
    echo -e "${BLUE}📦 $service: Downloading...${NC}"
    
    # Use pip wheel with optimizations
    pip wheel -r requirements.txt -w wheels/ --no-deps --disable-pip-version-check --quiet 2>/dev/null || {
        echo -e "${YELLOW}⚠️  $service: Some wheels failed, continuing...${NC}"
    }
    
    # Count results
    wheel_count=$(find wheels/ -name "*.whl" 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ $service: $wheel_count wheels ready${NC}"
    
    cd "../.."
}

echo -e "${BLUE}🚀 Fast wheels download starting...${NC}\n"

# Download for key services in parallel
{
    download_service_wheels_fast "api-gateway" &
    download_service_wheels_fast "data-bridge" &
    download_service_wheels_fast "ai-provider" &
    download_service_wheels_fast "trading-engine" &
    wait
}

{
    download_service_wheels_fast "ml-processing" &
    download_service_wheels_fast "deep-learning" &
    download_service_wheels_fast "user-service" &
    download_service_wheels_fast "ai-orchestration" &
    wait
}

echo -e "\n${GREEN}🎉 Wheels download completed for core services!${NC}"
echo -e "${BLUE}📊 Total wheels files:${NC}"
find ./services/*/wheels/ -name "*.whl" 2>/dev/null | wc -l

echo -e "\n${BLUE}Now deploying services with offline wheels...${NC}"