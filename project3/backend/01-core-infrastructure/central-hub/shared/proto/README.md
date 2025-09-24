# Protocol Buffers Schema Registry

## Overview
Centralized schema management for all inter-service communication using Protocol Buffers. Provides schema versioning, validation, and code generation for NATS, Kafka, and gRPC transport layers.

## Architecture

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Schema Registry   │────│  Schema Storage  │────│   Version Control   │
│   (Management API)  │    │   (PostgreSQL)   │    │     (Git-based)     │
└─────────────────────┘    └──────────────────┘    └─────────────────────┘
           │                                                    │
           ▼                                                    ▼
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Code Generation    │    │  Schema Cache    │    │   Schema Validation │
│  (Python/TS/etc)   │    │    (Redis)       │    │   (Compatibility)   │
└─────────────────────┘    └──────────────────┘    └─────────────────────┘
           │                          │                        │
           ▼                          ▼                        ▼
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│     Services        │    │   NATS/Kafka     │    │       gRPC          │
│   (Generated Code)  │    │  (Protobuf)      │    │   (Protobuf)        │
└─────────────────────┘    └──────────────────┘    └─────────────────────┘
```

## Directory Structure

```
schema-registry/
├── README.md                    # This file
├── docker-compose.yml           # Schema registry infrastructure
├── schemas/                     # Protocol buffer definitions
│   ├── common/                  # Shared data types
│   │   ├── timestamp.proto
│   │   ├── money.proto
│   │   └── user.proto
│   ├── trading/                 # Trading domain schemas
│   │   ├── market_data.proto
│   │   ├── orders.proto
│   │   ├── positions.proto
│   │   └── risk.proto
│   ├── ai/                      # AI/ML domain schemas
│   │   ├── predictions.proto
│   │   ├── features.proto
│   │   └── models.proto
│   └── system/                  # System/admin schemas
│       ├── config.proto
│       ├── health.proto
│       └── audit.proto
├── generated/                   # Generated code output
│   ├── python/
│   ├── typescript/
│   └── go/
├── scripts/                     # Automation scripts
│   ├── generate-code.sh
│   ├── validate-schemas.sh
│   └── deploy-schemas.sh
├── registry-service/            # Schema registry service
│   ├── main.py
│   ├── models/
│   ├── routes/
│   └── utils/
└── tests/                       # Schema validation tests
    ├── compatibility/
    └── integration/
```

## Schema Categories

### Category A: High-Volume Mission Critical
**Transport**: NATS + Kafka with Protocol Buffers
**Performance**: <1ms serialization, <15ms end-to-end

#### Trading Core Schemas:
- `trading/market_data.proto` - Tick data, OHLCV, market depth
- `trading/orders.proto` - Order placement, execution, cancellation
- `trading/positions.proto` - Position management, P&L updates
- `ai/predictions.proto` - AI trading signals, confidence scores

#### Example Schema:
```protobuf
// trading/market_data.proto
syntax = "proto3";
package trading.v1;

message TickData {
  string symbol = 1;
  double bid = 2;
  double ask = 3;
  double volume = 4;
  int64 timestamp_ms = 5;
  string tenant_id = 6;
}

message MarketDataStream {
  repeated TickData ticks = 1;
  string source = 2;
  int64 sequence_number = 3;
}
```

### Category B: Medium-Volume Important
**Transport**: gRPC with Protocol Buffers
**Performance**: <50ms response time

#### Business Logic Schemas:
- `common/user.proto` - User management, authentication
- `trading/portfolio.proto` - Portfolio views, analytics
- `ai/features.proto` - Technical indicators, feature data

#### Example Schema:
```protobuf
// ai/features.proto
syntax = "proto3";
package ai.v1;

message TechnicalIndicators {
  string symbol = 1;
  double rsi = 2;
  double macd = 3;
  double sma_20 = 4;
  double ema_50 = 5;
  BollingerBands bollinger = 6;
  int64 calculated_at = 7;
  string tenant_id = 8;
}

message BollingerBands {
  double upper = 1;
  double middle = 2;
  double lower = 3;
  double bandwidth = 4;
}
```

### Category C: Low-Volume Standard
**Transport**: HTTP REST + JSON
**Performance**: <500ms response time

#### Admin/Config Operations:
- `system/config.proto` - Configuration management
- `system/health.proto` - Health checks, monitoring
- `system/audit.proto` - Audit logs, compliance

## Schema Versioning Strategy

### Semantic Versioning
- **Major.Minor.Patch** (e.g., v1.2.3)
- **Major**: Breaking changes (field removal, type changes)
- **Minor**: Backward compatible additions (new fields)
- **Patch**: Documentation, non-functional changes

### Compatibility Rules
```yaml
Forward_Compatibility: # New code reads old data
  - New fields must be optional
  - Default values must be sensible
  - Enum values cannot be removed

Backward_Compatibility: # Old code reads new data
  - Cannot remove existing fields
  - Cannot change field types
  - Cannot change field numbers
```

### Migration Strategy
```yaml
Breaking_Changes:
  1. Create new schema version (v2)
  2. Deploy dual-version support
  3. Migrate consumers to v2
  4. Deprecate v1 after 30 days
  5. Remove v1 support after 90 days
```

## Multi-Tenant Schema Design

### Tenant Isolation
All schemas include `tenant_id` field for data isolation:

```protobuf
message BaseMessage {
  string tenant_id = 1;        // Required for all messages
  int64 timestamp_ms = 2;      // UTC timestamp
  string correlation_id = 3;   // Request tracing
}
```

### Tenant-Specific Configurations
```protobuf
message TenantConfig {
  string tenant_id = 1;
  RiskLimits risk_limits = 2;
  TradingSettings trading_settings = 3;
  AIModelConfig ai_config = 4;
}
```

## Schema Registry Service

### REST API Endpoints
```yaml
Schema_Management:
  GET    /schemas                    # List all schemas
  GET    /schemas/{subject}          # Get schema by subject
  GET    /schemas/{subject}/versions # Get all versions
  POST   /schemas/{subject}          # Register new schema
  DELETE /schemas/{subject}          # Delete schema subject

Compatibility:
  POST   /schemas/{subject}/compatibility  # Test compatibility
  GET    /config                          # Get global config
  PUT    /config                          # Update global config

Code_Generation:
  POST   /generate/{language}             # Generate code bindings
  GET    /generated/{language}/{version}  # Download generated code
```

### Service Configuration
```yaml
# docker-compose.yml excerpt
schema-registry:
  image: confluentinc/cp-schema-registry:latest
  environment:
    SCHEMA_REGISTRY_HOST_NAME: schema-registry
    SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:9092
    SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
  ports:
    - "8081:8081"
```

## Performance Specifications

### Serialization Performance
```yaml
Category_A_Performance:
  Binary_Size: "~70% smaller than JSON"
  Serialization: "<1ms for 1KB message"
  Deserialization: "<0.5ms for 1KB message"
  Memory_Usage: "50% less than JSON objects"

Category_B_Performance:
  gRPC_Overhead: "<5ms additional latency"
  HTTP2_Benefits: "Multiplexing, header compression"
  Streaming: "Bidirectional streaming support"
  Type_Safety: "Compile-time validation"
```

### Schema Registry Performance
```yaml
Registry_Performance:
  Schema_Lookup: "<10ms (cached), <100ms (database)"
  Code_Generation: "<30 seconds for full codebase"
  Validation: "<50ms for large schemas"
  Storage: "PostgreSQL + Redis caching"
```

## Development Workflow

### 1. Schema Development
```bash
# Create new schema
cd schemas/trading/
nano new_feature.proto

# Validate schema
./scripts/validate-schemas.sh trading/new_feature.proto

# Generate code
./scripts/generate-code.sh trading/new_feature.proto
```

### 2. Code Generation
```bash
# Generate for all languages
./scripts/generate-code.sh --all

# Generate for specific language
./scripts/generate-code.sh --python schemas/trading/

# Watch mode for development
./scripts/generate-code.sh --watch
```

### 3. Testing
```bash
# Compatibility testing
pytest tests/compatibility/

# Integration testing
pytest tests/integration/

# Performance testing
python tests/performance/benchmark_serialization.py
```

## Implementation Timeline

### Phase 1: Foundation (Days 1-2)
- [ ] Setup Schema Registry infrastructure
- [ ] Create base schema structure
- [ ] Implement code generation pipeline
- [ ] Basic validation and testing

### Phase 2: Core Schemas (Days 3-4)
- [ ] Trading domain schemas (Category A)
- [ ] AI/ML domain schemas (Category A)
- [ ] Business logic schemas (Category B)
- [ ] System schemas (Category C)

### Phase 3: Integration (Days 5-6)
- [ ] NATS/Kafka integration
- [ ] gRPC service definitions
- [ ] HTTP REST API schemas
- [ ] End-to-end testing

### Phase 4: Production (Days 7-8)
- [ ] Performance optimization
- [ ] Monitoring and alerting
- [ ] Documentation and training
- [ ] Production deployment

## Security Considerations

### Schema Access Control
```yaml
Access_Control:
  Schema_Read: "All authenticated services"
  Schema_Write: "Admin roles only"
  Code_Generation: "CI/CD pipeline only"
  Schema_Deletion: "Super admin only"
```

### Data Security
```yaml
Sensitive_Data:
  PII_Fields: "Marked with field options"
  Encryption: "Application-level encryption"
  Audit_Trail: "All schema changes logged"
  Compliance: "GDPR/CCPA field annotations"
```

## Monitoring and Alerts

### Key Metrics
```yaml
Schema_Registry_Metrics:
  - Schema registration rate
  - Code generation success rate
  - Compatibility test failures
  - Schema lookup latency
  - Storage utilization

Performance_Metrics:
  - Serialization/deserialization time
  - Message size distribution
  - Schema validation errors
  - Network bandwidth usage
```

### Alert Conditions
```yaml
Critical_Alerts:
  - Schema registry service down
  - Compatibility check failures
  - Code generation failures

Warning_Alerts:
  - High schema lookup latency
  - Increasing message sizes
  - Deprecated schema usage
```

## Best Practices

### Schema Design
1. **Keep schemas simple** - Single responsibility per message
2. **Use semantic versioning** - Clear version progression
3. **Design for evolution** - Optional fields, sensible defaults
4. **Include metadata** - Timestamps, tenant IDs, correlation IDs
5. **Document thoroughly** - Clear field descriptions

### Performance Optimization
1. **Minimize nesting** - Flat structures serialize faster
2. **Use appropriate types** - int32 vs int64, float vs double
3. **Batch when possible** - Repeated fields for bulk operations
4. **Cache generated code** - Avoid regeneration overhead
5. **Monitor message sizes** - Keep under 1MB for optimal performance

## Troubleshooting

### Common Issues
```yaml
Schema_Not_Found:
  Cause: "Schema not registered or wrong subject name"
  Solution: "Check schema registry, verify subject name"

Compatibility_Error:
  Cause: "Breaking changes in schema evolution"
  Solution: "Review compatibility rules, create new version"

Code_Generation_Failed:
  Cause: "Invalid protobuf syntax or missing dependencies"
  Solution: "Validate schema syntax, check imports"

Performance_Degradation:
  Cause: "Large message sizes or complex nesting"
  Solution: "Optimize schema design, reduce message size"
```

### Debug Commands
```bash
# Check schema registry health
curl http://localhost:8081/subjects

# Validate specific schema
protoc --proto_path=schemas --python_out=generated/python schemas/trading/orders.proto

# Test serialization performance
python tests/performance/benchmark_schema.py schemas/trading/market_data.proto

# Monitor schema usage
curl http://localhost:8081/metrics
```

## Support and Documentation

### Resources
- **Schema Registry API**: http://localhost:8081/docs
- **Generated Code Docs**: ./generated/docs/
- **Performance Benchmarks**: ./tests/performance/results/
- **Migration Guides**: ./docs/migrations/

### Contact
- **Schema Issues**: Create issue in schema-registry repository
- **Performance Questions**: Contact platform team
- **Breaking Changes**: Notify all service teams 48h in advance

---

This Schema Registry provides the foundation for all inter-service communication in the AI trading platform, ensuring type safety, performance, and reliability across all transport layers.