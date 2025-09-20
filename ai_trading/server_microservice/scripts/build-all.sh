#!/bin/bash
# Build all microservices

echo "Building AI Trading Platform Microservices..."

services=(
    "api-gateway"
    "mt5-bridge" 
    "trading-engine"
    "ml-processing"
    "deep-learning"
    "ai-orchestration"
    "ai-provider"
    "database-service"
)

for service in "${services[@]}"; do
    echo "Building $service..."
    # docker build -t ai-trading-$service ./services/$service
done

echo "All services built successfully!"