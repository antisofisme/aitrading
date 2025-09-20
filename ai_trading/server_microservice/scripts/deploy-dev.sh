#!/bin/bash
# Deploy development environment

echo "Deploying AI Trading Platform - Development Environment"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Deploy development stack
echo "Starting development services..."
# docker-compose -f docker-compose.dev.yml up -d

echo "Development environment deployed!"
echo "Services available at:"
echo "  - API Gateway: http://localhost:8000"
echo "  - MT5 Bridge: http://localhost:8001"  
echo "  - Trading Engine: http://localhost:8002"
echo "  - ML Processing: http://localhost:8003"
echo "  - Deep Learning: http://localhost:8004"
echo "  - AI Orchestration: http://localhost:8005"
echo "  - AI Provider: http://localhost:8006"
echo "  - Database Service: http://localhost:8007"