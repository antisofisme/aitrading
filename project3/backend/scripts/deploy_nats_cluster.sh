#!/bin/bash
# ================================================================
# NATS Cluster Deployment Script
# ================================================================
# Purpose: Deploy 3-node NATS cluster with zero downtime
# Usage: ./deploy_nats_cluster.sh
# ================================================================

set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  NATS Cluster Deployment"
echo "=============================================="
echo ""

# Check if old single NATS instance exists
if docker ps -a --filter "name=suho-nats-server" --format "{{.Names}}" | grep -q "suho-nats-server"; then
    echo -e "${YELLOW}⚠️  Old single NATS instance detected: suho-nats-server${NC}"
    echo "This will be stopped and removed..."
    echo ""

    # Stop old instance
    echo "Stopping old NATS instance..."
    docker-compose stop nats-server 2>/dev/null || echo "Already stopped"
    docker-compose rm -f nats-server 2>/dev/null || echo "Already removed"
    echo -e "${GREEN}✅ Old instance removed${NC}"
    echo ""
fi

# Deploy cluster
echo "=============================================="
echo "  Deploying NATS Cluster (3 nodes)"
echo "=============================================="
echo ""

# Start nodes sequentially (prevents race conditions)
echo "Starting nats-1 (primary node)..."
docker-compose up -d nats-1

echo "Waiting for nats-1 to be healthy (15s)..."
sleep 15

echo "Starting nats-2..."
docker-compose up -d nats-2

echo "Waiting for nats-2 to be healthy (10s)..."
sleep 10

echo "Starting nats-3..."
docker-compose up -d nats-3

echo "Waiting for nats-3 to be healthy (10s)..."
sleep 10

echo -e "${GREEN}✅ All nodes started${NC}"
echo ""

# Wait for cluster to form
echo "=============================================="
echo "  Waiting for Cluster Formation (30s)"
echo "=============================================="
sleep 30

# Verify cluster health
echo ""
echo "=============================================="
echo "  Verifying Cluster Health"
echo "=============================================="
echo ""

# Run health check
./scripts/monitor_nats_cluster.sh

# Check if cluster is healthy
running_count=$(docker ps --filter "name=suho-nats-" --filter "status=running" --format "{{.Names}}" | wc -l)

if [ "$running_count" -ne 3 ]; then
    echo ""
    echo -e "${RED}❌ Cluster deployment failed: Only $running_count/3 nodes running${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check logs: docker logs suho-nats-1 --tail 50"
    echo "2. Check logs: docker logs suho-nats-2 --tail 50"
    echo "3. Check logs: docker logs suho-nats-3 --tail 50"
    exit 1
fi

# Check cluster routes
routes_nats1=$(docker exec suho-nats-1 wget -qO- http://localhost:8222/routez 2>/dev/null | grep -o '"num_routes":[0-9]*' | cut -d: -f2 || echo "0")

if [ "$routes_nats1" -ne 2 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Warning: Cluster routes not fully formed (routes: $routes_nats1, expected: 2)${NC}"
    echo "Cluster may still be initializing. Check again in 30 seconds."
    echo ""
fi

# Restart services to reconnect to cluster
echo ""
echo "=============================================="
echo "  Restarting Services"
echo "=============================================="
echo ""

services_to_restart=(
    "historical-downloader"
    "live-collector"
    "data-bridge"
    "tick-aggregator"
    "external-data-collector"
    "api-gateway"
)

for service in "${services_to_restart[@]}"; do
    if docker ps --filter "name=suho-$service" --format "{{.Names}}" | grep -q "suho-$service"; then
        echo "Restarting $service..."
        docker-compose restart "$service" 2>/dev/null || echo "Service not found: $service"
    else
        echo "Skipping $service (not running)"
    fi
done

echo -e "${GREEN}✅ Services restarted${NC}"
echo ""

# Final status
echo "=============================================="
echo "  Deployment Complete"
echo "=============================================="
echo ""
echo -e "${GREEN}✅ NATS cluster deployed successfully!${NC}"
echo ""
echo "Cluster endpoints:"
echo "  - nats-1: nats://localhost:4222 (primary)"
echo "  - nats-2: nats://localhost:4223"
echo "  - nats-3: nats://localhost:4224"
echo ""
echo "Monitoring endpoints:"
echo "  - nats-1: http://localhost:8222"
echo "  - nats-2: http://localhost:8223"
echo "  - nats-3: http://localhost:8224"
echo ""
echo "Useful commands:"
echo "  - Monitor cluster: ./scripts/monitor_nats_cluster.sh"
echo "  - View logs: docker logs suho-nats-1 --tail 50 -f"
echo "  - Test failover: docker stop suho-nats-1 && sleep 10 && docker start suho-nats-1"
echo ""
echo "=============================================="

# Test failover capability (optional)
read -p "Do you want to test failover capability? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "=============================================="
    echo "  Testing Failover Capability"
    echo "=============================================="
    echo ""

    echo "Stopping nats-1 (primary node)..."
    docker stop suho-nats-1

    echo "Waiting 15 seconds for failover..."
    sleep 15

    echo "Checking if services reconnected to nats-2 or nats-3..."
    ./scripts/monitor_nats_cluster.sh

    echo ""
    echo "Starting nats-1 again..."
    docker start suho-nats-1

    echo "Waiting 10 seconds for nats-1 to rejoin cluster..."
    sleep 10

    echo ""
    echo "Final cluster status:"
    ./scripts/monitor_nats_cluster.sh

    echo ""
    echo -e "${GREEN}✅ Failover test complete!${NC}"
fi

echo ""
echo "Deployment finished!"
