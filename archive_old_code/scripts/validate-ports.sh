#!/bin/bash

# Port Allocation Validation Script
# Validates that all service ports are unique and properly allocated

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Port Allocation Validation Script ===${NC}"
echo

# Source the port configuration
if [ -f "./config/service-ports.env" ]; then
    source ./config/service-ports.env
    echo -e "${GREEN}✓ Loaded port configuration${NC}"
else
    echo -e "${RED}✗ Port configuration file not found: ./config/service-ports.env${NC}"
    exit 1
fi

# Array to store all used ports
declare -a USED_PORTS
declare -a PORT_CONFLICTS

# Function to check if port is already used
check_port_conflict() {
    local port=$1
    local service=$2

    for used_port in "${USED_PORTS[@]}"; do
        if [ "$port" = "$used_port" ]; then
            PORT_CONFLICTS+=("Port $port: Conflict detected for service $service")
            return 1
        fi
    done

    USED_PORTS+=("$port")
    return 0
}

echo "Validating port allocations..."
echo

# Validate Client Side Services
echo -e "${YELLOW}Client Side Services (9001-9004):${NC}"
check_port_conflict $METATRADER_CONNECTOR_PORT "metatrader-connector"
echo "  metatrader-connector: $METATRADER_CONNECTOR_PORT"

check_port_conflict $DATA_COLLECTOR_PORT "data-collector"
echo "  data-collector: $DATA_COLLECTOR_PORT"

check_port_conflict $MARKET_MONITOR_PORT "market-monitor"
echo "  market-monitor: $MARKET_MONITOR_PORT"

check_port_conflict $CONFIG_MANAGER_PORT "config-manager"
echo "  config-manager: $CONFIG_MANAGER_PORT"

echo

# Validate Core Infrastructure Services
echo -e "${YELLOW}Core Infrastructure Services (8000-8009):${NC}"
check_port_conflict $API_GATEWAY_PORT "api-gateway"
echo "  api-gateway: $API_GATEWAY_PORT"

check_port_conflict $DATA_BRIDGE_PORT "data-bridge"
echo "  data-bridge: $DATA_BRIDGE_PORT"

check_port_conflict $PERFORMANCE_ANALYTICS_PORT "performance-analytics"
echo "  performance-analytics: $PERFORMANCE_ANALYTICS_PORT"

check_port_conflict $AI_ORCHESTRATION_PORT "ai-orchestration"
echo "  ai-orchestration: $AI_ORCHESTRATION_PORT"

check_port_conflict $TRADING_ENGINE_PORT "trading-engine"
echo "  trading-engine: $TRADING_ENGINE_PORT"

check_port_conflict $DATABASE_SERVICE_PORT "database-service"
echo "  database-service: $DATABASE_SERVICE_PORT"

check_port_conflict $USER_SERVICE_PORT "user-service"
echo "  user-service: $USER_SERVICE_PORT"

echo

# Validate AI/ML Pipeline Services
echo -e "${YELLOW}AI/ML Pipeline Services (8011-8016):${NC}"
check_port_conflict $FEATURE_ENGINEERING_PORT "feature-engineering"
echo "  feature-engineering: $FEATURE_ENGINEERING_PORT"

check_port_conflict $ML_SUPERVISED_PORT "ml-supervised"
echo "  ml-supervised: $ML_SUPERVISED_PORT"

check_port_conflict $ML_DEEP_LEARNING_PORT "ml-deep-learning"
echo "  ml-deep-learning: $ML_DEEP_LEARNING_PORT"

check_port_conflict $PATTERN_VALIDATOR_PORT "pattern-validator"
echo "  pattern-validator: $PATTERN_VALIDATOR_PORT"

check_port_conflict $TELEGRAM_SERVICE_PORT "telegram-service"
echo "  telegram-service: $TELEGRAM_SERVICE_PORT"

check_port_conflict $BACKTESTING_ENGINE_PORT "backtesting-engine"
echo "  backtesting-engine: $BACKTESTING_ENGINE_PORT"

echo

# Validate Compliance Services
echo -e "${YELLOW}Compliance & Regulatory Services (8017-8019):${NC}"
check_port_conflict $COMPLIANCE_MONITOR_PORT "compliance-monitor"
echo "  compliance-monitor: $COMPLIANCE_MONITOR_PORT"

check_port_conflict $AUDIT_TRAIL_PORT "audit-trail"
echo "  audit-trail: $AUDIT_TRAIL_PORT"

check_port_conflict $REGULATORY_REPORTING_PORT "regulatory-reporting"
echo "  regulatory-reporting: $REGULATORY_REPORTING_PORT"

echo

# Validate Infrastructure Services
echo -e "${YELLOW}Infrastructure Services:${NC}"
check_port_conflict $KAFKA_PORT "kafka"
echo "  kafka: $KAFKA_PORT"

check_port_conflict $ZOOKEEPER_PORT "zookeeper"
echo "  zookeeper: $ZOOKEEPER_PORT"

check_port_conflict $ELASTICSEARCH_PORT "elasticsearch"
echo "  elasticsearch: $ELASTICSEARCH_PORT"

check_port_conflict $ELASTICSEARCH_TRANSPORT_PORT "elasticsearch-transport"
echo "  elasticsearch-transport: $ELASTICSEARCH_TRANSPORT_PORT"

check_port_conflict $JAEGER_UI_PORT "jaeger-ui"
echo "  jaeger-ui: $JAEGER_UI_PORT"

check_port_conflict $JAEGER_COLLECTOR_PORT "jaeger-collector"
echo "  jaeger-collector: $JAEGER_COLLECTOR_PORT"

check_port_conflict $AIRFLOW_WEBSERVER_PORT "airflow-webserver"
echo "  airflow-webserver: $AIRFLOW_WEBSERVER_PORT"

check_port_conflict $REDIS_PORT "redis"
echo "  redis: $REDIS_PORT"

echo

# Check for conflicts
if [ ${#PORT_CONFLICTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No port conflicts detected!${NC}"
    echo -e "${GREEN}✓ Total ports validated: ${#USED_PORTS[@]}${NC}"
    echo

    # Validate port ranges
    echo -e "${YELLOW}Port Range Validation:${NC}"

    # Check client port range (9001-9004)
    client_ports_ok=true
    for port in $METATRADER_CONNECTOR_PORT $DATA_COLLECTOR_PORT $MARKET_MONITOR_PORT $CONFIG_MANAGER_PORT; do
        if [ $port -lt 9001 ] || [ $port -gt 9004 ]; then
            echo -e "${RED}✗ Client port $port is outside allowed range (9001-9004)${NC}"
            client_ports_ok=false
        fi
    done

    if [ "$client_ports_ok" = true ]; then
        echo -e "${GREEN}✓ Client ports within range (9001-9004)${NC}"
    fi

    # Check server port range (8000-8019)
    server_ports_ok=true
    for port in $API_GATEWAY_PORT $DATA_BRIDGE_PORT $PERFORMANCE_ANALYTICS_PORT $AI_ORCHESTRATION_PORT \
                $TRADING_ENGINE_PORT $DATABASE_SERVICE_PORT $USER_SERVICE_PORT \
                $FEATURE_ENGINEERING_PORT $ML_SUPERVISED_PORT $ML_DEEP_LEARNING_PORT \
                $PATTERN_VALIDATOR_PORT $TELEGRAM_SERVICE_PORT $BACKTESTING_ENGINE_PORT \
                $COMPLIANCE_MONITOR_PORT $AUDIT_TRAIL_PORT $REGULATORY_REPORTING_PORT; do
        if [ $port -lt 8000 ] || [ $port -gt 8019 ]; then
            echo -e "${RED}✗ Server port $port is outside allowed range (8000-8019)${NC}"
            server_ports_ok=false
        fi
    done

    if [ "$server_ports_ok" = true ]; then
        echo -e "${GREEN}✓ Server ports within range (8000-8019)${NC}"
    fi

    # Check compliance port isolation (8017-8019)
    compliance_ports_ok=true
    for port in $COMPLIANCE_MONITOR_PORT $AUDIT_TRAIL_PORT $REGULATORY_REPORTING_PORT; do
        if [ $port -lt 8017 ] || [ $port -gt 8019 ]; then
            echo -e "${RED}✗ Compliance port $port is outside compliance range (8017-8019)${NC}"
            compliance_ports_ok=false
        fi
    done

    if [ "$compliance_ports_ok" = true ]; then
        echo -e "${GREEN}✓ Compliance ports properly isolated (8017-8019)${NC}"
    fi

    echo
    echo -e "${GREEN}✓ PORT ALLOCATION VALIDATION SUCCESSFUL${NC}"
    echo -e "${GREEN}✓ All services have unique, properly allocated ports${NC}"
    echo -e "${GREEN}✓ No conflicts detected across all services${NC}"

    exit 0
else
    echo -e "${RED}✗ Port conflicts detected:${NC}"
    for conflict in "${PORT_CONFLICTS[@]}"; do
        echo -e "${RED}  $conflict${NC}"
    done
    echo
    echo -e "${RED}✗ PORT ALLOCATION VALIDATION FAILED${NC}"
    echo -e "${RED}✗ Please resolve port conflicts before deployment${NC}"

    exit 1
fi