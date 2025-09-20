#!/bin/bash
# Clean wheel libraries: keep only Python 3.11, Linux, and service-relevant packages

echo "🧹 Cleaning wheel libraries for optimal deployment..."

# Function to clean wheels for a service
clean_service_wheels() {
    local service_dir=$1
    local service_name=$2
    
    if [ ! -d "$service_dir/wheels" ]; then
        echo "❌ No wheels directory found for $service_name"
        return
    fi
    
    echo "📦 Cleaning $service_name wheels..."
    cd "$service_dir/wheels"
    
    local total_before=$(ls -1 *.whl 2>/dev/null | wc -l)
    
    # Remove non-Python 3.11 wheels (keep cp311 and py3-none-any)
    echo "  🐍 Removing non-Python 3.11 wheels..."
    find . -name "*.whl" | grep -E "cp31[02]|cp39|cp38|cp37|cp36|cp35" | grep -v cp311 | xargs rm -f 2>/dev/null
    
    # Remove non-Linux wheels (keep linux, manylinux, and none-any)
    echo "  🐧 Removing non-Linux wheels..."
    find . -name "*.whl" | grep -E "win32|win_amd64|macosx|any32" | xargs rm -f 2>/dev/null
    
    # Remove unnecessary wheels based on service type
    case $service_name in
        "api-gateway")
            echo "  🚪 Removing heavy ML/AI libraries from API Gateway..."
            find . -name "*.whl" | grep -E "torch|tensorflow|sklearn|numpy|pandas|scipy|matplotlib|opencv" | head -10 | xargs rm -f 2>/dev/null
            ;;
        "user-service")
            echo "  👤 Removing ML/AI libraries from User Service..."
            find . -name "*.whl" | grep -E "torch|tensorflow|sklearn|numpy|pandas|scipy|matplotlib|opencv" | head -10 | xargs rm -f 2>/dev/null
            ;;
        "database-service")
            echo "  🗄️ Keeping database-relevant libraries only..."
            find . -name "*.whl" | grep -E "torch|tensorflow|opencv|matplotlib" | head -10 | xargs rm -f 2>/dev/null
            ;;
        "data-bridge")
            echo "  🌉 Keeping data processing libraries..."
            # Keep most libraries as data-bridge needs various tools
            ;;
        "ai-orchestration"|"ai-provider")
            echo "  🤖 Keeping AI libraries..."
            # Keep AI/ML libraries
            ;;
        "deep-learning"|"ml-processing")
            echo "  🧠 Keeping ML/DL libraries..."
            # Keep all ML/AI libraries
            ;;
        "trading-engine")
            echo "  📈 Keeping trading calculation libraries..."
            find . -name "*.whl" | grep -E "opencv|matplotlib" | xargs rm -f 2>/dev/null
            ;;
    esac
    
    local total_after=$(ls -1 *.whl 2>/dev/null | wc -l)
    local removed=$((total_before - total_after))
    
    echo "  ✅ $service_name: $total_before → $total_after wheels (removed $removed)"
    
    cd - > /dev/null
}

# Clean wheels for each service
SERVICES=(
    "services/api-gateway:api-gateway"
    "services/user-service:user-service" 
    "services/database-service:database-service"
    "services/data-bridge:data-bridge"
    "services/ai-orchestration:ai-orchestration"
    "services/ai-provider:ai-provider"
    "services/deep-learning:deep-learning"
    "services/ml-processing:ml-processing"
    "services/trading-engine:trading-engine"
)

total_removed=0
for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r service_dir service_name <<< "$service_info"
    clean_service_wheels "$service_dir" "$service_name"
done

echo ""
echo "🎉 Wheel cleaning completed!"
echo "📊 This should significantly reduce Docker build times and image sizes."
echo ""
echo "Next steps:"
echo "1. Test build: docker-compose build --parallel"
echo "2. Deploy: docker-compose up -d"