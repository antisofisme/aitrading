#!/bin/bash
# ================================================================
# NATS Cluster Health Monitor
# ================================================================
# Purpose: Check health and status of NATS 3-node cluster
# Usage: ./monitor_nats_cluster.sh
# ================================================================

set -e

echo "=============================================="
echo "  NATS Cluster Health Check"
echo "=============================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if container is running
check_container() {
    local node=$1
    local container="suho-$node"

    echo -e "${BLUE}Checking $node...${NC}"

    # Check if container is running
    if docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "^$container$"; then
        echo -e "  ${GREEN}✅ Container: Running${NC}"

        # Check health endpoint
        health=$(docker exec "$container" wget -qO- http://localhost:8222/healthz 2>/dev/null || echo "error")
        if [ "$health" = "ok" ]; then
            echo -e "  ${GREEN}✅ Health: OK${NC}"
        else
            echo -e "  ${RED}❌ Health: Failed${NC}"
        fi

        # Get cluster info (routes)
        routes=$(docker exec "$container" wget -qO- http://localhost:8222/routez 2>/dev/null | grep -o '"num_routes":[0-9]*' | cut -d: -f2 || echo "0")
        if [ "$routes" = "2" ]; then
            echo -e "  ${GREEN}✅ Cluster Routes: $routes (expected: 2)${NC}"
        elif [ "$routes" -gt "0" ]; then
            echo -e "  ${YELLOW}⚠️  Cluster Routes: $routes (expected: 2, cluster forming)${NC}"
        else
            echo -e "  ${RED}❌ Cluster Routes: $routes (cluster not formed)${NC}"
        fi

        # Get connection count
        conns=$(docker exec "$container" wget -qO- http://localhost:8222/connz 2>/dev/null | grep -o '"num_connections":[0-9]*' | cut -d: -f2 || echo "0")
        echo -e "  ${BLUE}📊 Client Connections: $conns${NC}"

        # Get server info (name, version)
        server_info=$(docker exec "$container" wget -qO- http://localhost:8222/varz 2>/dev/null)
        server_name=$(echo "$server_info" | grep -o '"server_name":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        version=$(echo "$server_info" | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo -e "  ${BLUE}📋 Server: $server_name | Version: $version${NC}"

    else
        echo -e "  ${RED}❌ Container: Not running${NC}"
    fi
    echo ""
}

# Check all nodes
check_container "nats-1"
check_container "nats-2"
check_container "nats-3"

# Overall cluster status
echo "=============================================="
echo "  Cluster Summary"
echo "=============================================="

running_count=$(docker ps --filter "name=suho-nats-" --filter "status=running" --format "{{.Names}}" | wc -l)

if [ "$running_count" -eq 3 ]; then
    echo -e "${GREEN}✅ All 3 nodes are running${NC}"
elif [ "$running_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Only $running_count/3 nodes are running${NC}"
else
    echo -e "${RED}❌ No NATS nodes are running${NC}"
fi

# Check if services are connected
echo ""
echo "=============================================="
echo "  Service Connections"
echo "=============================================="

# Get total connections across all nodes
total_conns=0
for node in nats-1 nats-2 nats-3; do
    container="suho-$node"
    if docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "^$container$"; then
        conns=$(docker exec "$container" wget -qO- http://localhost:8222/connz 2>/dev/null | grep -o '"num_connections":[0-9]*' | cut -d: -f2 || echo "0")
        total_conns=$((total_conns + conns))
    fi
done

echo -e "${BLUE}📊 Total Client Connections: $total_conns${NC}"

# Expected services: historical-downloader, live-collector, data-bridge (3 instances), tick-aggregator, external-data-collector
expected_min=6
if [ "$total_conns" -ge "$expected_min" ]; then
    echo -e "${GREEN}✅ Services connected (expected: $expected_min+, actual: $total_conns)${NC}"
elif [ "$total_conns" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some services connected ($total_conns/$expected_min+)${NC}"
else
    echo -e "${RED}❌ No services connected${NC}"
fi

echo ""
echo "=============================================="
echo "  Quick Commands"
echo "=============================================="
echo "View nats-1 logs:    docker logs suho-nats-1 --tail 50"
echo "View nats-2 logs:    docker logs suho-nats-2 --tail 50"
echo "View nats-3 logs:    docker logs suho-nats-3 --tail 50"
echo "Restart cluster:     docker-compose restart nats-1 nats-2 nats-3"
echo "View routing info:   docker exec suho-nats-1 wget -qO- http://localhost:8222/routez | jq"
echo "=============================================="
