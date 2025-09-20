#\!/bin/bash
# Fix offline deployment - install with wheels + PyPI fallback

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

fix_service_installation() {
    local service=$1
    
    echo -e "${BLUE}🔧 Fixing $service installation${NC}"
    
    # Create smarter install script
    cat > "services/$service/install-wheels.sh" << 'EOI'
#\!/bin/bash
echo "📦 Installing from wheels with PyPI fallback..."

# Try wheels first, fallback to PyPI if missing dependencies
if [ -d "wheels" ] && [ "$(ls -A wheels)" ]; then
    echo "Installing from local wheels + PyPI fallback..."
    pip install --find-links wheels/ -r requirements.txt --quiet
else
    echo "Installing from PyPI..."
    pip install -r requirements.txt --quiet
fi
echo "✅ Installation completed"
EOI
    
    chmod +x "services/$service/install-wheels.sh"
    echo -e "${GREEN}   ✅ Updated $service install script${NC}"
}

# Fix all services
services=("user-service" "data-bridge" "trading-engine" "database-service" "ai-provider" "ai-orchestration")

for service in "${services[@]}"; do
    if [ -d "./services/$service" ]; then
        fix_service_installation "$service"
    fi
done

echo -e "\n${GREEN}🎉 All services fixed for wheels + PyPI fallback deployment${NC}"
EOF < /dev/null
