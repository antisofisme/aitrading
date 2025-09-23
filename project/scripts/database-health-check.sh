#!/bin/bash

# Database Health Check Script for AI Trading Platform
# Validates all database connections and reports status

set -e

echo "🔍 AI Trading Platform - Database Health Check"
echo "============================================="
echo

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Health check results
declare -a results=()

# Function to check service health
check_service() {
    local service_name=$1
    local check_command=$2
    local container_name=$3

    echo -n "🔹 Checking $service_name... "

    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        if eval "$check_command" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ HEALTHY${NC}"
            results+=("$service_name:HEALTHY")
        else
            echo -e "${RED}❌ UNHEALTHY${NC}"
            results+=("$service_name:UNHEALTHY")
        fi
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        results+=("$service_name:NOT_RUNNING")
    fi
}

# Check PostgreSQL
check_service "PostgreSQL" \
    "docker exec ai-trading-postgres pg_isready -U ai_trading_user -d ai_trading" \
    "ai-trading-postgres"

# Check Redis
check_service "Redis" \
    "docker exec ai-trading-redis redis-cli ping | grep -q PONG" \
    "ai-trading-redis"

# Check ClickHouse
check_service "ClickHouse" \
    "docker exec ai-trading-clickhouse clickhouse-client --query 'SELECT 1'" \
    "ai-trading-clickhouse"

# Check MongoDB
check_service "MongoDB" \
    "docker exec ai-trading-mongo mongosh --quiet --eval 'db.adminCommand(\"ping\")'" \
    "ai-trading-mongo"

# Check InfluxDB
check_service "InfluxDB" \
    "docker exec ai-trading-influxdb influx ping | grep -q OK" \
    "ai-trading-influxdb"

echo
echo "📊 Health Check Summary:"
echo "========================"

healthy_count=0
total_count=${#results[@]}

for result in "${results[@]}"; do
    service=${result%:*}
    status=${result#*:}

    case $status in
        "HEALTHY")
            echo -e "✅ $service: ${GREEN}HEALTHY${NC}"
            ((healthy_count++))
            ;;
        "UNHEALTHY")
            echo -e "❌ $service: ${RED}UNHEALTHY${NC}"
            ;;
        "NOT_RUNNING")
            echo -e "🔴 $service: ${RED}NOT RUNNING${NC}"
            ;;
    esac
done

echo
echo "📈 Overall Status: $healthy_count/$total_count databases healthy"

if [ $healthy_count -eq $total_count ]; then
    echo -e "${GREEN}🎉 All databases are healthy!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some databases need attention${NC}"
    exit 1
fi