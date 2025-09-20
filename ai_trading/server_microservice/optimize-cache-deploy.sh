#!/bin/bash
echo "🔧 Optimizing Docker Cache and Wheels Strategy"
echo "================================================"

# Stop current build
echo "1️⃣ Stopping current build..."
docker-compose down --remove-orphans

# Show current Docker image status
echo "2️⃣ Current Docker images:"
docker images | head -10

# Strategy explanation
echo ""
echo "🎯 OPTIMAL CACHE STRATEGY:"
echo "✅ Base Image (python:3.11): Cached once globally"
echo "✅ Wheels Layer: Cached until wheels/ changes" 
echo "✅ Requirements Layer: Cached until requirements.txt changes"
echo "✅ Application Layer: Rebuild only when code changes"
echo ""

# Use Docker Buildkit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "3️⃣ Starting optimized deployment with cache strategy..."
echo "   - Using DOCKER_BUILDKIT=1 for advanced caching"
echo "   - Offline-first wheels installation"
echo "   - Layer-optimized Dockerfile structure"
echo ""

# Deploy without --build flag to use cache when possible
docker-compose up -d

echo "4️⃣ Monitoring deployment progress..."
echo "   - Use 'docker-compose logs -f' to follow logs"
echo "   - Use 'docker images' to see cached layers"
echo ""