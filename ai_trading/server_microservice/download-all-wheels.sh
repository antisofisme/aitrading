#!/bin/bash
# Download wheels untuk semua microservice
# Agar deployment jadi offline dan cepat

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Services yang perlu wheels
SERVICES=(
    "api-gateway"
    "data-bridge"
    "ai-orchestration"
    "deep-learning"
    "ai-provider"
    "ml-processing"
    "trading-engine"
    "database-service"
    "user-service"
)

download_service_wheels() {
    local service=$1
    local service_dir="./services/$service"
    
    echo -e "${BLUE}📦 Downloading wheels for $service${NC}"
    
    if [ ! -f "$service_dir/requirements.txt" ]; then
        echo -e "${RED}   ❌ No requirements.txt found for $service${NC}"
        return 1
    fi
    
    # Create wheels directory if not exists
    mkdir -p "$service_dir/wheels"
    
    # Download wheels dengan fallback ke PyPI
    cd "$service_dir"
    
    echo -e "${YELLOW}   📥 Downloading dependencies...${NC}"
    if pip wheel -r requirements.txt -w wheels/ --no-deps; then
        # Get size
        wheels_size=$(du -sh wheels/ | cut -f1)
        wheels_count=$(find wheels/ -name "*.whl" | wc -l)
        echo -e "${GREEN}   ✅ Downloaded $wheels_count wheels ($wheels_size)${NC}"
        cd "../.."
        return 0
    else
        echo -e "${RED}   ❌ Failed to download wheels for $service${NC}"
        cd "../.."
        return 1
    fi
}

echo -e "${BLUE}🚀 Starting wheels download for all microservices${NC}\n"

successful_downloads=0
total_services=${#SERVICES[@]}

for service in "${SERVICES[@]}"; do
    if [ -d "./services/$service" ]; then
        if download_service_wheels "$service"; then
            ((successful_downloads++))
        fi
    else
        echo -e "${YELLOW}⚠️  Service directory ./services/$service not found${NC}"
    fi
    echo "---"
done

echo -e "\n${BLUE}📊 Download Summary:${NC}"
echo -e "${GREEN}✅ Successfully downloaded wheels: $successful_downloads/$total_services services${NC}"

# Show total wheels size
echo -e "\n${BLUE}💾 Total wheels size:${NC}"
find ./services/*/wheels/ -name "*.whl" 2>/dev/null | wc -l | xargs echo "Total wheel files:"
du -sh ./services/*/wheels/ 2>/dev/null | awk '{sum+=$1} END {print "Total size: ~" sum}'

echo -e "\n${GREEN}🎉 Wheels download completed!${NC}"
echo -e "${BLUE}Now deployment will be much faster (offline mode)${NC}"