#!/bin/bash
# Health Check and Dependency Management Test Script
# Tests startup ordering, health checks, dependency failure, and recovery

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "HEALTH CHECK AND DEPENDENCY MANAGEMENT TEST"
echo "=========================================================================="
echo ""

# Test 1: Clean Start
echo -e "${BLUE}TEST 1: Clean Start - Verifying Startup Order${NC}"
echo "--------------------------------------------------------------------------"
echo "Cleaning up any existing containers..."
docker-compose down -v

echo ""
echo "Starting all services..."
docker-compose up -d

echo ""
echo "Waiting 60 seconds for services to initialize..."
sleep 60

echo ""
echo "Checking service health status..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep suho

echo ""
echo -e "${GREEN}✓ Test 1 Complete${NC}"
echo ""
sleep 5

# Test 2: Verify Health Checks
echo -e "${BLUE}TEST 2: Verify Health Checks${NC}"
echo "--------------------------------------------------------------------------"
echo "Checking which services are healthy..."

HEALTHY_COUNT=$(docker ps --filter health=healthy | grep suho | wc -l)
TOTAL_COUNT=$(docker ps | grep suho | wc -l)

echo "Healthy services: $HEALTHY_COUNT / $TOTAL_COUNT"
docker ps --filter health=healthy --format "table {{.Names}}\t{{.Status}}"

if [ "$HEALTHY_COUNT" -eq "$TOTAL_COUNT" ]; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
else
    echo -e "${YELLOW}⚠ Some services are not healthy yet, waiting additional 30s...${NC}"
    sleep 30
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep suho
fi

echo ""
echo -e "${GREEN}✓ Test 2 Complete${NC}"
echo ""
sleep 5

# Test 3: Dependency Failure - ClickHouse
echo -e "${BLUE}TEST 3: Dependency Failure - ClickHouse${NC}"
echo "--------------------------------------------------------------------------"
echo "Stopping ClickHouse to simulate failure..."
docker-compose stop suho-clickhouse

echo ""
echo "Waiting 20 seconds for health checks to detect failure..."
sleep 20

echo ""
echo "Checking dependent service health (tick-aggregator, data-bridge should be unhealthy)..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "suho-(tick-aggregator|data-bridge|historical-downloader)"

echo ""
echo -e "${GREEN}✓ Test 3 Complete - Dependent services should show unhealthy${NC}"
echo ""
sleep 5

# Test 4: Recovery
echo -e "${BLUE}TEST 4: Recovery - Restarting ClickHouse${NC}"
echo "--------------------------------------------------------------------------"
echo "Restarting ClickHouse..."
docker-compose start suho-clickhouse

echo ""
echo "Waiting 60 seconds for recovery..."
sleep 60

echo ""
echo "Checking if dependent services recovered..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "suho-(tick-aggregator|data-bridge|historical-downloader|clickhouse)"

echo ""
echo -e "${GREEN}✓ Test 4 Complete - Services should recover to healthy${NC}"
echo ""
sleep 5

# Test 5: Check Logs for Connection Errors
echo -e "${BLUE}TEST 5: Check Logs for Connection Errors${NC}"
echo "--------------------------------------------------------------------------"
echo "Checking tick-aggregator logs for connection errors..."
echo ""
docker logs suho-tick-aggregator --tail 50 | grep -i error || echo "No errors found"

echo ""
echo "Checking data-bridge logs for connection errors..."
echo ""
docker logs suho-data-bridge --tail 50 | grep -i error || echo "No errors found"

echo ""
echo -e "${GREEN}✓ Test 5 Complete${NC}"
echo ""

# Summary
echo "=========================================================================="
echo "TEST SUMMARY"
echo "=========================================================================="
echo ""
echo "Final service status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep suho

echo ""
echo -e "${GREEN}✓ All tests completed!${NC}"
echo ""
echo "Key Observations:"
echo "1. Services should start in dependency order (databases → central-hub → application services)"
echo "2. Health checks should report 'healthy' status after initialization"
echo "3. Dependent services should detect failures and report 'unhealthy'"
echo "4. Services should recover automatically when dependencies are restored"
echo "5. Logs should show retry attempts with exponential backoff (1s, 2s, 4s, 8s, 16s, 30s)"
echo ""
echo "=========================================================================="
