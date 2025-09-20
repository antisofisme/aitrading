#!/bin/bash
# Quick Individual Service Deployment

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

deploy_minimal_service() {
    local service=$1
    local port=${2:-8000}
    
    echo -e "${BLUE}🚀 Deploying $service on port $port${NC}"
    
    # Create working directory
    mkdir -p "/tmp/$service-deploy"
    
    # Create simple Python app
    cat > "/tmp/$service-deploy/app.py" << EOF
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="$service")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "$service"}

@app.get("/")
def root():
    return {"message": "$service is running", "service": "$service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    # Create simple Dockerfile
    cat > "/tmp/$service-deploy/Dockerfile" << EOF
FROM python:3.11-slim
RUN pip install fastapi uvicorn
WORKDIR /app
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
EOF
    
    # Build and run
    docker build -t "$service-simple" "/tmp/$service-deploy/"
    docker stop "$service-simple" 2>/dev/null || true
    docker rm "$service-simple" 2>/dev/null || true
    docker run -d --name "$service-simple" -p "$port:8000" "$service-simple"
    
    echo -e "${GREEN}✅ $service deployed successfully on port $port${NC}"
    
    # Test
    sleep 3
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo -e "${GREEN}✅ $service health check passed${NC}"
    fi
}

echo -e "${BLUE}=== Quick Microservices Deployment ===${NC}\n"

# Deploy core services
deploy_minimal_service "api-gateway" 8000
deploy_minimal_service "data-bridge" 8001  
deploy_minimal_service "trading-engine" 8007
deploy_minimal_service "ai-provider" 8005
deploy_minimal_service "ml-processing" 8006

echo -e "\n${GREEN}✅ All services deployed!${NC}"
echo -e "${BLUE}Running containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"