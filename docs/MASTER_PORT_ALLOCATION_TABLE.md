# Master Port Allocation Table - AI Trading Platform

## Port Assignment Strategy

This document defines the authoritative port allocation for all services in the AI Trading Platform to prevent conflicts and ensure consistent deployment.

## Core Infrastructure Services (8000-8009)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| api-gateway | 8000 | Node.js | Main API Gateway | LEVEL_1 |
| data-bridge | 8001 | Python | Market Data Bridge | LEVEL_1 |
| performance-analytics | 8002 | Python | Performance Monitoring | LEVEL_1 |
| ai-orchestration | 8003 | Python | AI Coordination Hub | LEVEL_1 |
| configuration-service | 8004 | Node.js | Dynamic Configuration | LEVEL_1 |
| notification-service | 8005 | Node.js | Real-time Notifications | LEVEL_1 |
| database-service | 8006 | Node.js | Database Management | LEVEL_1 |
| trading-engine | 8007 | Python | Core Trading Logic | LEVEL_1 |
| websocket-gateway | 8008 | Node.js | WebSocket Communication | LEVEL_2 |
| load-balancer | 8009 | Node.js | Internal Load Balancing | LEVEL_2 |

## Data Processing Services (8010-8019)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| data-ingestion | 8010 | Python | Data Collection | LEVEL_3 |
| feature-engineering | 8011 | Python | ML Feature Processing | LEVEL_3 |
| data-validation | 8012 | Python | Data Quality Control | LEVEL_3 |
| historical-data | 8013 | Python | Historical Data Management | LEVEL_3 |
| real-time-processor | 8014 | Python | Real-time Data Processing | LEVEL_3 |
| data-warehouse | 8015 | Java | Data Warehousing | LEVEL_3 |
| etl-pipeline | 8016 | Python | ETL Operations | LEVEL_3 |
| data-backup | 8017 | Java | Data Backup Services | LEVEL_3 |
| data-recovery | 8018 | Java | Data Recovery Services | LEVEL_3 |
| data-archival | 8019 | Java | Data Archival | LEVEL_3 |

## AI/ML Services (8020-8029)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| ml-supervised | 8020 | Python | Supervised Learning | LEVEL_4 |
| ml-ensemble | 8021 | Python | Ensemble Models | LEVEL_4 |
| ml-deep-learning | 8022 | Python | Deep Learning Models | LEVEL_4 |
| pattern-validator | 8023 | Python | Pattern Recognition | LEVEL_4 |
| backtesting-engine | 8024 | Python | Strategy Backtesting | LEVEL_4 |
| model-registry | 8025 | Python | ML Model Management | LEVEL_4 |
| inference-engine | 8026 | Python | Model Inference | LEVEL_4 |
| model-trainer | 8027 | Python | Model Training | LEVEL_4 |
| hyperparameter-tuner | 8028 | Python | Hyperparameter Optimization | LEVEL_4 |
| ai-explainability | 8029 | Python | AI Explanations | LEVEL_4 |

## Communication Services (8030-8039)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| telegram-service | 8030 | Python | Telegram Integration | LEVEL_5 |
| email-service | 8031 | Node.js | Email Notifications | LEVEL_5 |
| sms-service | 8032 | Node.js | SMS Notifications | LEVEL_5 |
| webhook-service | 8033 | Node.js | Webhook Management | LEVEL_5 |
| alert-manager | 8034 | Python | Alert Management | LEVEL_5 |
| message-queue | 8035 | Java | Message Queuing | LEVEL_2 |
| event-bus | 8036 | Java | Event Processing | LEVEL_2 |
| pub-sub | 8037 | Java | Publish/Subscribe | LEVEL_2 |
| socket-manager | 8038 | Node.js | Socket Connection Management | LEVEL_2 |
| communication-hub | 8039 | Node.js | Unified Communications | LEVEL_5 |

## Compliance & Security Services (8040-8049)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| compliance-monitor | 8040 | Java | Compliance Monitoring | COMPLIANCE |
| audit-trail | 8041 | Java | Audit Logging | COMPLIANCE |
| regulatory-reporting | 8042 | Java | Regulatory Reports | COMPLIANCE |
| security-scanner | 8043 | Java | Security Scanning | COMPLIANCE |
| threat-detection | 8044 | Java | Threat Detection | COMPLIANCE |
| access-control | 8045 | Java | Access Management | COMPLIANCE |
| encryption-service | 8046 | Java | Encryption Services | COMPLIANCE |
| key-management | 8047 | Java | Key Management | COMPLIANCE |
| identity-provider | 8048 | Java | Identity Management | COMPLIANCE |
| security-audit | 8049 | Java | Security Auditing | COMPLIANCE |

## Business Services (8050-8059)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| user-management | 8050 | Node.js | User Management | BUSINESS |
| subscription-service | 8051 | Node.js | Subscription Management | BUSINESS |
| payment-gateway | 8052 | Node.js | Payment Processing | BUSINESS |
| billing-service | 8053 | Node.js | Billing Management | BUSINESS |
| revenue-analytics | 8054 | Python | Revenue Analytics | BUSINESS |
| usage-monitoring | 8055 | Python | Usage Tracking | BUSINESS |
| customer-support | 8056 | Node.js | Customer Support | BUSINESS |
| crm-integration | 8057 | Node.js | CRM Integration | BUSINESS |
| analytics-dashboard | 8058 | Node.js | Business Analytics | BUSINESS |
| reporting-service | 8059 | Python | Business Reporting | BUSINESS |

## Development & Monitoring (8060-8069)

| Service | Port | Technology | Description | Level |
|---------|------|------------|-------------|-------|
| monitoring-dashboard | 8060 | Node.js | System Monitoring | DEV |
| metrics-collector | 8061 | Python | Metrics Collection | DEV |
| log-aggregator | 8062 | Java | Log Aggregation | DEV |
| health-checker | 8063 | Node.js | Health Monitoring | DEV |
| performance-profiler | 8064 | Python | Performance Profiling | DEV |
| error-tracker | 8065 | Node.js | Error Tracking | DEV |
| deployment-manager | 8066 | Node.js | Deployment Management | DEV |
| ci-cd-orchestrator | 8067 | Node.js | CI/CD Pipeline | DEV |
| test-runner | 8068 | Python | Test Execution | DEV |
| code-quality | 8069 | Java | Code Quality Analysis | DEV |

## Reserved Ports (8070-8099)

Ports 8070-8099 are reserved for future expansion and temporary services.

## External Service Integrations

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| Redis | 6379 | TCP | Cache and Session Store |
| PostgreSQL | 5432 | TCP | Primary Database |
| MongoDB | 27017 | TCP | Document Database |
| InfluxDB | 8086 | HTTP | Time Series Database |
| Grafana | 3000 | HTTP | Monitoring Dashboard |
| Prometheus | 9090 | HTTP | Metrics Collection |
| RabbitMQ | 5672 | AMQP | Message Broker |
| Elasticsearch | 9200 | HTTP | Search and Analytics |
| Kibana | 5601 | HTTP | Log Visualization |

## Port Conflict Resolution History

### Previous Conflicts Resolved:
1. **ml-ensemble vs business-api**: ml-ensemble moved from 8014 → 8021
2. **backtesting-engine vs telegram-service**: telegram-service moved from 8016 → 8030
3. **compliance services spacing**: All compliance services moved to 8040-8049 range
4. **business services consolidation**: All business services moved to 8050-8059 range

## Usage Guidelines

1. **Never reuse ports** - Each service must have a unique port
2. **Follow category ranges** - Keep services in their designated port ranges
3. **Update this document** - Any port changes must be reflected here first
4. **Validate deployments** - Check this table before deploying new services
5. **Environment consistency** - Use same ports across dev/staging/production

## Environment-Specific Overrides

### Development Environment
- All services can run on localhost with assigned ports
- Docker Compose should use these exact port mappings

### Staging/Production
- Services may be behind load balancers
- Internal communication should still use these ports
- External access controlled via reverse proxy

## Validation Commands

```bash
# Check for port conflicts in current deployment
netstat -tulpn | grep -E ":(80[0-9]{2})" | sort

# Validate Docker Compose port assignments
docker-compose config | grep -E "^\s*-\s*\"80[0-9]{2}:"

# Check service availability
for port in {8000..8069}; do nc -z localhost $port && echo "Port $port is in use"; done
```

## Maintenance

This document should be updated whenever:
- New services are added to the platform
- Services are removed or deprecated
- Port conflicts are discovered
- Technology stack changes occur

**Last Updated**: 2025-09-21
**Next Review**: 2025-10-21