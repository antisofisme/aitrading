#!/bin/bash

echo "🔧 Emergency Service Recovery Script"
echo "=================================="

# Function to test service
test_service() {
    local port=$1
    local name=$2
    echo -n "Testing $name ($port): "
    if curl -s --connect-timeout 2 http://localhost:$port/health >/dev/null; then
        echo "✅ UP"
        return 0
    else
        echo "❌ DOWN"
        return 1
    fi
}

# Test all services
echo "📊 Current Service Status:"
test_service 8000 "api-gateway"
test_service 8001 "data-bridge" 
test_service 8003 "ai-orchestration"
test_service 8004 "deep-learning"
test_service 8005 "ai-provider"
test_service 8006 "ml-processing"
test_service 8007 "trading-engine"
test_service 8008 "database-service"
test_service 8009 "user-service"

echo ""
echo "🚀 Attempting to start failed services..."

# Function to start and test service
start_service() {
    local service=$1
    local port=$2
    
    echo "Starting $service..."
    docker-compose up -d --no-deps $service 2>/dev/null
    sleep 3
    
    if curl -s --connect-timeout 2 http://localhost:$port/health >/dev/null; then
        echo "✅ $service started successfully"
    else
        echo "❌ $service failed to start, checking logs..."
        docker logs service-$service --tail 3
        echo ""
    fi
}

# Start failed services
start_service "trading-engine" 8007
start_service "ai-orchestration" 8003

echo ""
echo "📊 Final Status Check:"
for port in {8000..8009}; do
    case $port in
        8000) name="api-gateway" ;;
        8001) name="data-bridge" ;;
        8003) name="ai-orchestration" ;;
        8004) name="deep-learning" ;;
        8005) name="ai-provider" ;;
        8006) name="ml-processing" ;;
        8007) name="trading-engine" ;;
        8008) name="database-service" ;;
        8009) name="user-service" ;;
        *) continue ;;
    esac
    test_service $port $name
done

echo ""
echo "✅ Service recovery script completed"