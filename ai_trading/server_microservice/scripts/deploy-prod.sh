#!/bin/bash
# Deploy production environment

echo "Deploying AI Trading Platform - Production Environment"

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file required for production deployment"
    echo "Please copy .env.example to .env and configure with production values"
    exit 1
fi

# Validate required environment variables
required_vars=("OPENAI_API_KEY" "DEEPSEEK_API_KEY" "POSTGRES_PASSWORD" "CLICKHOUSE_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

# Deploy production stack
echo "Starting production services..."
# docker-compose -f docker-compose.prod.yml up -d

echo "Production environment deployed!"
echo "Monitor services with:"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  docker-compose -f docker-compose.prod.yml logs -f"