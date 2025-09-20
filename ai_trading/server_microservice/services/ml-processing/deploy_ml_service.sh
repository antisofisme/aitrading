#!/bin/bash

# ML Processing Service Deployment Script
# Deploys the ML Processing service with real ML capabilities

set -e

echo "🤖 Deploying ML Processing Service..."
echo "=================================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="ml-processing-service"

# Configuration
CONTAINER_NAME="${SERVICE_NAME}"
DOCKER_IMAGE="${SERVICE_NAME}:latest"
SERVICE_PORT="8006"
HOST_PORT="8006"

echo "📁 Working directory: $SCRIPT_DIR"
echo "🐳 Container name: $CONTAINER_NAME"
echo "🎯 Service port: $SERVICE_PORT"

# Function to check if container exists
container_exists() {
    docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Step 1: Stop and remove existing container
echo ""
echo "1. Cleaning up existing deployment..."
if container_running; then
    echo "   Stopping running container..."
    docker stop "${CONTAINER_NAME}"
fi

if container_exists; then
    echo "   Removing existing container..."
    docker rm "${CONTAINER_NAME}"
fi

# Step 2: Build new image
echo ""
echo "2. Building ML Processing service image..."
docker build -f Dockerfile.wheels -t "${DOCKER_IMAGE}" .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker image built successfully"

# Step 3: Deploy new container
echo ""
echo "3. Deploying ML Processing service..."

docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${HOST_PORT}:${SERVICE_PORT}" \
    -e ENVIRONMENT=production \
    -e SERVICE_NAME=ml-processing \
    -e SERVICE_PORT=8006 \
    -e LOG_LEVEL=INFO \
    "${DOCKER_IMAGE}"

if [ $? -ne 0 ]; then
    echo "❌ Container deployment failed!"
    exit 1
fi

echo "✅ Container deployed successfully"

# Step 4: Wait for service to start
echo ""
echo "4. Waiting for service to start..."
sleep 10

# Step 5: Health check
echo ""
echo "5. Performing health check..."

max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "   Attempt $attempt/$max_attempts..."
    
    if curl -s -f http://localhost:${HOST_PORT}/health > /dev/null; then
        echo "✅ Health check passed!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Health check failed after $max_attempts attempts"
        echo "📋 Container logs:"
        docker logs "${CONTAINER_NAME}" --tail 20
        exit 1
    fi
    
    sleep 5
    ((attempt++))
done

# Step 6: Display service information
echo ""
echo "📊 Service Information:"
echo "   Container: $CONTAINER_NAME"
echo "   Image: $DOCKER_IMAGE"
echo "   Port: http://localhost:$HOST_PORT"
echo "   Health: http://localhost:$HOST_PORT/health"
echo "   API Docs: http://localhost:$HOST_PORT/docs"
echo "   Status: http://localhost:$HOST_PORT/status"

# Step 7: Test ML endpoints
echo ""
echo "6. Testing ML Processing endpoints..."

echo "   Testing root endpoint..."
curl -s http://localhost:${HOST_PORT}/ | jq '.service' || echo "Root endpoint accessible"

echo "   Testing algorithms endpoint..."
curl -s http://localhost:${HOST_PORT}/api/v1/ml-processing/algorithms | jq '.real_ml_available' || echo "Algorithms endpoint accessible"

# Step 8: Display container status
echo ""
echo "📋 Container Status:"
docker ps | head -1
docker ps | grep "${CONTAINER_NAME}"

echo ""
echo "🎉 ML Processing Service Deployment Complete!"
echo "=================================================="
echo ""
echo "🚀 Service is now running at: http://localhost:$HOST_PORT"
echo "📚 API Documentation: http://localhost:$HOST_PORT/docs"
echo "🏥 Health Check: http://localhost:$HOST_PORT/health"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker logs $CONTAINER_NAME"
echo "   Stop service: docker stop $CONTAINER_NAME"
echo "   Restart service: docker restart $CONTAINER_NAME"
echo "   Remove service: docker rm -f $CONTAINER_NAME"
echo ""
echo "🧪 Test integration:"
echo "   python test_ml_integration.py"
echo ""