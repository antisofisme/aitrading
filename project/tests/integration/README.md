# Plan2 Microservices Integration Tests

Comprehensive integration test suite for the Plan2 microservices architecture, validating inter-service communication, data flow, and error handling across the entire system.

## Overview

This test suite validates the following key aspects of the Plan2 architecture:

- **Service Registry**: Configuration Service as central registry and service discovery
- **API Gateway Routing**: Request routing and load balancing to backend services
- **Database Service Integration**: Multi-database operations (PostgreSQL, MongoDB, Redis)
- **Flow Registry Communication**: Flow creation, execution, and cross-service orchestration
- **Error Propagation**: Flow-Aware Error Handling across service boundaries
- **End-to-End Microservices Mesh**: Complete service mesh functionality

## Quick Start

```bash
# Install dependencies
npm install

# Run all integration tests with comprehensive test runner
node test-runner.js

# Run individual test suites
npx mocha service-registry.test.js --timeout 30000
npx mocha api-gateway-routing.test.js --timeout 45000
npx mocha database-service.test.js --timeout 60000
npx mocha flow-registry.test.js --timeout 45000
npx mocha error-propagation.test.js --timeout 60000
npx mocha microservices-mesh.test.js --timeout 90000

# Run with debug output
LOG_LEVEL=debug node test-runner.js
```

## Test Suites

### 1. Service Registry Tests (`service-registry.test.js`)
- Service registration and discovery through Configuration Service
- Health monitoring and status checks across all services
- Configuration management and multi-tenant isolation
- Service dependency resolution and communication patterns
- Dynamic service registration/deregistration

### 2. API Gateway Routing Tests (`api-gateway-routing.test.js`)
- Dynamic service route discovery and load balancing
- Authentication and authorization across all endpoints
- Rate limiting with different user tiers (basic/premium)
- Request/response transformation and header injection
- Circuit breaker patterns and failover handling
- Health check routing and service availability

### 3. Database Service Tests (`database-service.test.js`)
- **PostgreSQL**: CRUD operations, transactions, complex joins
- **MongoDB**: Document operations, aggregations, updates
- **Redis**: Key-value operations, hashes, lists, TTL management
- Cross-database operations and distributed transactions
- Data synchronization between different database types
- Concurrent operations and performance under load
- Error handling and transaction rollbacks

### 4. Flow Registry Tests (`flow-registry.test.js`)
- Flow definition, registration, and validation
- Flow execution with real-time monitoring via WebSocket
- Cross-service communication through flow orchestration
- Parallel execution and complex dependency management
- Flow versioning, rollouts, and A/B testing
- Flow metrics, analytics, and performance tracking

### 5. Error Propagation Tests (`error-propagation.test.js`)
- HTTP error code propagation across service boundaries
- Flow-aware error context maintenance and correlation
- Distributed transaction rollbacks and compensating actions
- Circuit breaker activation and service isolation
- Retry strategies with exponential backoff and jitter
- Error monitoring, alerting, and correlation analysis

### 6. End-to-End Microservices Mesh Tests (`microservices-mesh.test.js`)
- Complete user journey workflows (registration → trading → analytics)
- Real-time data streaming with WebSocket connections
- Cross-service event propagation and processing
- Performance testing under concurrent load
- Data consistency and ACID properties validation
- Security enforcement and access control across services

## Prerequisites

### Required Services
Ensure the following services are running before executing tests:

```bash
# Configuration Service (Service Registry)
port 3001 - http://localhost:3001

# API Gateway
port 3000 - http://localhost:3000

# Database Service
port 3002 - http://localhost:3002

# Additional services for full mesh testing:
# User Service: port 3003
# Trading Service: port 3004
# Portfolio Service: port 3005
# Analytics Service: port 3006
# Notification Service: port 3007
```

### Required Databases
- **PostgreSQL**: Test database for relational data operations
- **MongoDB**: Test database for document operations
- **Redis**: Test database for caching and real-time data

### Environment Variables
```bash
# Service URLs (optional, defaults provided)
CONFIG_SERVICE_URL=http://localhost:3001
API_GATEWAY_URL=http://localhost:3000
DATABASE_SERVICE_URL=http://localhost:3002

# Database Configuration
TEST_PG_HOST=localhost
TEST_PG_PORT=5432
TEST_PG_DATABASE=test_trading_db
TEST_PG_USER=test_user
TEST_PG_PASSWORD=test_password

TEST_REDIS_HOST=localhost
TEST_REDIS_PORT=6379
TEST_REDIS_DB=1

# Test Configuration
LOG_LEVEL=info  # debug, info, warn, error, quiet
TEST_TIMEOUT=60000
```

## Running Tests

### Prerequisites

1. **Node.js 18+** installed
2. **PostgreSQL** running (for database tests)
3. **Foundation services** running (optional, tests will indicate status)

### Environment Setup

```bash
# Set environment variables (optional)
export NODE_ENV=test
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
```

### Test Execution

```bash
# Full integration test with orchestrator
npm test

# Individual test suites
npm run test:api-gateway      # API Gateway only
npm run test:database         # Database Service only
npm run test:data-bridge      # Data Bridge only
npm run test:central-hub      # Central Hub only
npm run test:workspace        # Configuration only

# Filtered test runs
npm run test:critical         # Only critical services
npm run test:quick           # Quick validation
```

## Test Results

### Output Formats

1. **Console Output** - Real-time test progress and results
2. **JSON Results** - Detailed results saved to `results/` directory
3. **Coverage Reports** - Code coverage (if applicable)

### Interpreting Results

The orchestrator provides a comprehensive summary:

```
📊 LEVEL 1 Foundation Integration Test Summary
==============================================

🧪 Test Execution:
   Total Tests: 45
   Passed: 42 (93.33%)
   Failed: 2
   Skipped: 1
   Duration: 67.45s

🏥 Service Health:
   🟢 API Gateway: healthy (critical)
   🟢 Database Service: healthy (critical)
   🟡 Data Bridge: unhealthy
   🟢 Central Hub: healthy (critical)

🎯 Foundation Readiness:
   LEVEL 1 Complete: ✅ YES
   Ready for LEVEL 2: ✅ YES
```

### Status Indicators

- 🟢 **Green** - Service healthy and tests passing
- 🟡 **Yellow** - Service has issues but not critical
- 🔴 **Red** - Critical service failing

## Performance Benchmarks

The tests include performance validation:

- **Fast Response**: < 100ms (health checks)
- **Acceptable Response**: < 500ms (API calls)
- **Slow Threshold**: < 2000ms (complex operations)

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Ensure configured ports are available
   - Check for other services using the same ports

2. **Database Connection Failures**
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure databases exist

3. **Service Not Available**
   - Check if services are running
   - Verify configuration matches test expectations
   - Check firewall settings

### Debug Mode

Run tests with additional logging:

```bash
DEBUG=true npm test
NODE_ENV=development npm run test:api-gateway
```

## Integration with LEVEL 2

Once LEVEL 1 tests pass with 90%+ success rate:

1. **Foundation Solid** - Core services are stable
2. **Ready for Connectivity** - Can proceed to LEVEL 2 integration
3. **Configuration Validated** - Service orchestration working
4. **Performance Benchmarked** - Baseline metrics established

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add performance benchmarks
3. Include error handling validation
4. Update configuration as needed
5. Document any new dependencies

## Files Structure

```
tests/integration/
├── config/
│   ├── test-config.js       # Main configuration
│   └── jest.setup.js        # Jest setup
├── utils/
│   └── test-helpers.js      # Shared utilities
├── suites/
│   ├── api-gateway.test.js
│   ├── database-service.test.js
│   ├── data-bridge.test.js
│   ├── central-hub.test.js
│   └── workspace-config.test.js
├── results/                 # Test results (generated)
├── orchestrator.js          # Main test runner
├── package.json
└── README.md
```

---

**Next Steps**: After LEVEL 1 validation, proceed to LEVEL 2 Connectivity integration tests.