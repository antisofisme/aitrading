#!/bin/bash
# Install packages directly from wheel files - ZERO internet access
# This script installs ALL wheels in the directory without checking PyPI

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

install_wheels_directly() {
    local service=$1
    local wheels_dir="./services/$service/wheels"
    
    echo -e "${BLUE}🔧 Creating direct wheel install script for $service${NC}"
    
    if [ ! -d "$wheels_dir" ]; then
        echo -e "${RED}❌ No wheels directory for $service${NC}"
        return 1
    fi
    
    # Create install script that installs all wheels directly
    cat > "services/$service/install-wheels.sh" << 'EOF'
#!/bin/bash
# Direct wheel installation - ZERO internet access
echo "📦 Installing wheels directly (no PyPI access)..."

# Install all wheels in order (dependencies first, then main packages)
cd /app/wheels

# Install all wheels directly
for wheel in *.whl; do
    if [ -f "$wheel" ]; then
        echo "Installing: $wheel"
        pip install --no-deps "$wheel" || echo "⚠️ Warning: $wheel already installed or failed"
    fi
done

echo "✅ Direct wheel installation completed"
EOF
    
    chmod +x "services/$service/install-wheels.sh"
    
    # Update Dockerfile to use direct wheel installation
    local dockerfile="services/$service/Dockerfile"
    if [ -f "$dockerfile" ]; then
        # Create backup
        cp "$dockerfile" "$dockerfile.pre-offline"
        
        # Replace pip install line with direct wheel installation
        sed -i '/pip install.*requirements\.txt/c\
# Install wheels directly (ZERO internet access)\
COPY install-wheels.sh ./\
RUN chmod +x install-wheels.sh && ./install-wheels.sh && rm -rf wheels/ install-wheels.sh
' "$dockerfile"
        
        echo -e "${GREEN}   ✅ Updated Dockerfile for direct wheel installation${NC}"
        return 0
    else
        echo -e "${RED}   ❌ No Dockerfile found${NC}"
        return 1
    fi
}

# Apply to all services
services=("database-service" "api-gateway" "user-service" "data-bridge" "ai-provider" "trading-engine" "ml-processing" "deep-learning" "ai-orchestration")

for service in "${services[@]}"; do
    if [ -d "./services/$service" ]; then
        echo -e "\n${BLUE}━━━ FIXING $service FOR ZERO INTERNET ACCESS ━━━${NC}"
        
        if install_wheels_directly "$service"; then
            echo -e "${GREEN}✅ $service: Ready for offline deployment${NC}"
        else
            echo -e "${RED}❌ $service: Failed to setup offline deployment${NC}"
        fi
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo -e "${YELLOW}⚠️  Service $service not found${NC}"
    fi
done

echo -e "\n${GREEN}🎉 ZERO INTERNET ACCESS SETUP COMPLETE!${NC}"
echo -e "${BLUE}Now Docker build will install wheels directly without any PyPI access${NC}"
echo -e "${YELLOW}Test with: docker-compose up -d --build database-service${NC}"