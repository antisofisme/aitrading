#!/bin/bash
#
# Data Bridge Scaling Script
# Scale data-bridge service to N instances for load balancing
#
# Usage:
#   ./scale_instances.sh [N]  # Scale to N instances (default: 3)
#

set -e  # Exit on error

# Color codes for pretty output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default number of instances
REPLICAS=${1:-3}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Data Bridge Scaling Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to backend directory
cd "$(dirname "$0")/../../../" || exit 1

echo -e "${YELLOW}📊 Current data-bridge status:${NC}"
docker-compose ps data-bridge 2>/dev/null || echo "No instances running"
echo ""

echo -e "${YELLOW}⚡ Scaling data-bridge to ${REPLICAS} instances...${NC}"
docker-compose up -d --scale data-bridge=${REPLICAS} --no-recreate

echo ""
echo -e "${YELLOW}⏳ Waiting for instances to start (15s)...${NC}"
sleep 15

echo ""
echo -e "${YELLOW}🔍 Checking instance health:${NC}"
docker-compose ps --filter "name=data-bridge" --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${YELLOW}📊 Instance details:${NC}"
docker ps --filter "name=data-bridge" --format "{{.Names}}: {{.Status}}" | while read -r line; do
    echo -e "  ${GREEN}✓${NC} $line"
done

echo ""
echo -e "${YELLOW}📡 Kafka consumer group info:${NC}"
echo "  Consumer Group: data-bridge-group"
echo "  Expected partition distribution: ~33% per instance (with 6 partitions)"

# Try to check Kafka consumer group (requires kafka-consumer-groups.sh in container)
echo ""
echo -e "${YELLOW}🔍 Checking Kafka partition assignment...${NC}"
if docker exec suho-kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group data-bridge-group 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Kafka partition assignment retrieved"
else
    echo -e "${YELLOW}⚠${NC}  Cannot retrieve Kafka info (this is normal if instances haven't consumed yet)"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Scaling complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Monitor logs: ${BLUE}docker-compose logs -f data-bridge${NC}"
echo -e "  2. Check metrics in Central Hub heartbeat logs"
echo -e "  3. Verify load distribution across instances"
echo -e "  4. Test failover: Stop one instance and verify others take over"
echo ""
echo -e "To scale to different number:"
echo -e "  ${BLUE}./scale_instances.sh 5${NC}  # Scale to 5 instances"
echo ""
echo -e "To stop all instances:"
echo -e "  ${BLUE}docker-compose stop data-bridge${NC}"
echo ""
