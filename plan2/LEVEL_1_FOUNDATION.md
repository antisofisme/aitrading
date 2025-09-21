# LEVEL 1 - FOUNDATION: Technical Infrastructure & Architecture

## 1.1 Architecture Pattern: Hybrid AI-Enhanced Microservices

### Foundation Pattern
- **Existing**: 11 production microservices + 22 completed ML components
- **Enhancement**: Probabilistic AI pipeline with 68-75% accuracy
- **Deployment**: Multi-tier service architecture with Redis caching + Docker orchestration
- **Communication**: Event-driven (Kafka/NATS) + REST APIs + WebSocket + gRPC + ML inference APIs

### Event-Driven Architecture Layer
```yaml
Event Streaming Platform:
  Primary: Apache Kafka (high-throughput trading events)
  Secondary: NATS (low-latency internal messaging)

Event Store:
  Technology: EventStore or Apache Pulsar
  Purpose: Event sourcing for audit compliance
  Retention: 7 years (regulatory requirement)

Event Patterns:
  - Domain Events: TradingExecuted, RiskThresholdBreached
  - Integration Events: MarketDataReceived, MLPredictionGenerated
  - Command Events: ExecuteTrade, UpdateRiskLimits
```

### Circuit Breaker & Resilience Patterns
```yaml
Circuit Breaker Implementation:
  Library: Hystrix (Java services) / Circuit Breaker (Python)
  Proxy: Envoy Proxy with circuit breaking
  Timeouts: 5s (fast), 30s (normal), 60s (heavy operations)

Resilience Strategies:
  - Bulkhead Pattern: Isolate critical trading operations
  - Retry with Exponential Backoff: Network failures
  - Graceful Degradation: Fallback to cached predictions
  - Health Checks: Circuit breaker state monitoring
```

## 1.2 Multi-Tier Storage Architecture

### Primary Database Strategy
```yaml
PostgreSQL (via Database Service 8008):
  - User accounts and authentication
  - Trading strategies and configurations
  - System logs and audit trails
  - Multi-tenant subscription management
  - ML model metadata and versioning
  - User-specific model configurations
  - Billing and usage tracking
  - Critical audit trails (7-year retention)
  - Regulatory compliance records

ClickHouse (via Database Service 8008):
  - High-frequency trading data
  - Time-series market data
  - Performance metrics and analytics
  - Probability scores from 5 ML models
  - Market regime classification history
  - Cross-asset correlation matrices
  - Model performance calibration data
  - Time-series log data storage (hot/warm tiers)
  - Real-time analytics and aggregations

Redis (via ML Business Service 8014):
  - Real-time ML inference caching
  - Rate limiting and throttling
  - User session management
  - Model prediction cache with TTL
  - Usage analytics aggregation
  - API key authentication
```

### Multi-Tier Log Storage Strategy
```yaml
Tier 1 - Hot Storage (DragonflyDB + Redis):
  Purpose: Real-time log access and analytics
  Retention: 24 hours
  Access Pattern: <1ms query latency
  Storage: DragonflyDB (primary) + Redis (backup)
  Capacity: 100GB per node
  Replication: 3x for high availability
  Cost: $150/month per TB

Tier 2 - Warm Storage (ClickHouse):
  Purpose: Short-term analytics and investigation
  Retention: 30 days
  Access Pattern: <100ms query latency
  Storage: ClickHouse with LZ4 compression
  Capacity: 10TB cluster
  Compression Ratio: 8:1 average
  Cost: $75/month per TB

Tier 3 - Cold Archive (S3 Glacier/Azure Archive):
  Purpose: Regulatory compliance and long-term storage
  Retention: 7 years (regulatory requirement)
  Access Pattern: <5s query latency
  Storage: Cloud object storage with archive tier
  Compression: Parquet format with ZSTD compression
  Compression Ratio: 15:1 average
  Cost: $4/month per TB
```

## 1.3 Docker Architecture Foundation

### Client Compose Infrastructure
```yaml
version: '3.8'
services:
  metatrader-connector:
    build: ./client/metatrader-connector
    ports: ["9001:9001"]
    environment:
      - MT5_LOGIN=${MT5_LOGIN}
      - MT5_PASSWORD=${MT5_PASSWORD}
      - MT5_SERVER=${MT5_SERVER}
      - BACKEND_URL=http://server-api-gateway:8000
    volumes:
      - mt5_data:/app/data
      - ./client/config:/app/config

  data-collector:
    build: ./client/data-collector
    ports: ["9002:9002"]
    depends_on: [metatrader-connector]
    environment:
      - DATA_SOURCES=mt5,news,economic_calendar
      - BACKEND_URL=http://server-api-gateway:8000

  market-monitor:
    build: ./client/market-monitor
    ports: ["9003:9003"]
    depends_on: [data-collector]
    environment:
      - MONITOR_PAIRS=EURUSD,GBPUSD,USDJPY,XAUUSD
      - ALERT_THRESHOLDS=${ALERT_THRESHOLDS}

  config-manager:
    build: ./client/config-manager
    ports: ["9004:9004"]
    volumes:
      - ./client/config:/app/config
      - client_logs:/app/logs
```

### Server Compose Infrastructure
```yaml
version: '3.8'
services:
  # TIER 1: Core Services
  api-gateway:
    build: ./server/api-gateway
    ports: ["8000:8000"]
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - AI_RATE_LIMITING=true
    depends_on: [database-service]

  database-service:
    build: ./server/database-service
    ports: ["8008:8008"]
    environment:
      - POSTGRES_URL=${POSTGRES_URL}
      - CLICKHOUSE_URL=${CLICKHOUSE_URL}
      - DRAGONFLYDB_URL=${DRAGONFLYDB_URL}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - ARANGODB_URL=${ARANGODB_URL}

  data-bridge:
    build: ./server/data-bridge
    ports: ["8001:8001"]
    environment:
      - MT5_WEBSOCKET_ENABLED=true
      - MULTI_SOURCE_ENABLED=true
    depends_on: [database-service]

  trading-engine:
    build: ./server/trading-engine
    ports: ["8007:8007"]
    environment:
      - AI_DECISIONS_ENABLED=true
      - ML_PIPELINE_URL=http://ml-supervised:8013
      - RISK_MANAGEMENT_LEVEL=strict
    depends_on: [database-service, ml-supervised, pattern-validator]
```

## 1.4 Network Security Infrastructure

### Zero Trust Security Model
```yaml
API Gateway (8000) - Enhanced:
  - OAuth2/OIDC with Auth0 or Keycloak
  - JWT token validation with short expiry (15 min)
  - Multi-factor authentication for trading operations
  - Adaptive rate limiting based on user behavior
  - IP allowlisting for production trading

Service Mesh Security:
  - Istio or Linkerd service mesh
  - Mutual TLS (mTLS) for all service communication
  - Service identity and certificate management
  - Network policies and microsegmentation
  - Zero trust network access (ZTNA)

Data Security - 2024 Standards:
  - Database encryption at rest (AES-256)
  - Field-level encryption for PII
  - API encryption in transit (TLS 1.3)
  - End-to-end encryption for sensitive data
  - Hardware Security Modules (HSM) for key management
  - Data loss prevention (DLP) policies
  - GDPR/CCPA compliance automation
```

### Docker Network Security
```yaml
Docker Network:
  - Internal service communication
  - External access only via API Gateway
  - Service discovery via DNS
  - Container isolation

Port Exposure:
  Client Side: 9001-9004 (local only)
  Server Side: 8000 (public), 8001-8019 (internal only)
  Database: Internal network only
  Compliance: 8017-8019 (internal compliance network)
```