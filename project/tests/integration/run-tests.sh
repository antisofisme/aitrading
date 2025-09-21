#!/bin/bash

# LEVEL 1 Foundation Integration Test Runner
# Quick validation script for foundation services

echo "🚀 LEVEL 1 Foundation Integration Test Runner"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the tests/integration directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Create results directory
mkdir -p results logs

# Set test environment
export NODE_ENV=test

echo ""
echo "🔍 Running Foundation Service Validation..."

# Test each service individually with timeout
echo ""
echo "1️⃣ Testing API Gateway (Port 3001)..."
timeout 30s npx jest suites/api-gateway.test.js --verbose --no-cache 2>/dev/null || echo "   ⚠️  API Gateway tests failed or service unavailable"

echo ""
echo "2️⃣ Testing Database Service (Port 8008)..."
timeout 30s npx jest suites/database-service.test.js --verbose --no-cache 2>/dev/null || echo "   ⚠️  Database Service tests failed or service unavailable"

echo ""
echo "3️⃣ Testing Data Bridge Service (Port 5001)..."
timeout 30s npx jest suites/data-bridge.test.js --verbose --no-cache 2>/dev/null || echo "   ⚠️  Data Bridge tests failed or service unavailable"

echo ""
echo "4️⃣ Testing Central Hub Service (Port 7000)..."
timeout 30s npx jest suites/central-hub.test.js --verbose --no-cache 2>/dev/null || echo "   ⚠️  Central Hub tests failed or service unavailable"

echo ""
echo "5️⃣ Testing Workspace Configuration..."
timeout 30s npx jest suites/workspace-config.test.js --verbose --no-cache 2>/dev/null || echo "   ⚠️  Workspace Configuration tests failed"

echo ""
echo "📊 Running Full Orchestrator..."
node orchestrator.js

echo ""
echo "✅ Integration test run complete!"
echo "📄 Check results/ directory for detailed reports"