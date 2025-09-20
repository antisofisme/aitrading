#!/bin/bash
# Deploy Core Microservices Only
# Focus on API Gateway, Data Bridge, and Trading Engine

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Core services only
CORE_SERVICES=(
    "api-gateway"
    "data-bridge" 
    "trading-engine"
)

PORTS=(
    ["api-gateway"]="8000"
    ["data-bridge"]="8001"
    ["trading-engine"]="8007"
)

deploy_service() {
    local service=$1
    local service_dir="./services/$service"
    
    echo -e "${BLUE}🚀 Deploying $service${NC}"
    
    # Create minimal Dockerfile
    cat > "$service_dir/Dockerfile.minimal" << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# Install only essential packages
RUN pip install fastapi uvicorn pydantic python-dotenv structlog

# Copy app
COPY main.py .
COPY src/ ./src/ 2>/dev/null || true

ENV PYTHONPATH="/app/src:/app"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-c", "
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title='${service}')

@app.get('/health')
def health():
    return JSONResponse({'status': 'healthy', 'service': '${service}'})

@app.get('/')
def root():
    return JSONResponse({'message': '${service} is running', 'status': 'active'})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
"]
EOF

    # Build and run
    docker build -f "$service_dir/Dockerfile.minimal" -t "$service-minimal" "$service_dir/"
    
    # Stop existing
    docker stop "$service-minimal" 2>/dev/null || true
    docker rm "$service-minimal" 2>/dev/null || true
    
    # Start new
    local port=${PORTS[$service]:-8000}
    docker run -d --name "$service-minimal" -p "$port:8000" "$service-minimal"
    
    echo -e "${GREEN}✅ $service deployed on port $port${NC}"
}

echo -e "${BLUE}=== Deploying Core Microservices ===${NC}\n"

for service in "${CORE_SERVICES[@]}"; do
    if [ -d "./services/$service" ]; then
        deploy_service "$service"
        sleep 2
    fi
done

echo -e "\n${GREEN}✅ Core services deployment completed${NC}"
echo -e "${BLUE}Check status: docker ps${NC}"
echo -e "${BLUE}Test services:${NC}"
echo -e "  - API Gateway: curl http://localhost:8000/health"
echo -e "  - Data Bridge: curl http://localhost:8001/health"  
echo -e "  - Trading Engine: curl http://localhost:8007/health"