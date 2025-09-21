# LEVEL 1 Foundation Integration Tests

This test suite validates the foundational services of the AI Trading Platform to ensure they are solid and ready for LEVEL 2 Connectivity integration.

## Overview

The LEVEL 1 Foundation consists of:

1. **API Gateway** (Port 3001) - Central routing and security layer
2. **Multi-Database Setup** (PostgreSQL) - 5 specialized databases
3. **Data Bridge Service** (Port 5001) - Real-time data connectivity
4. **Central Hub Service** (Port 7000) - Service discovery and health monitoring
5. **Workspace Configuration** - Service orchestration and configuration management

## Quick Start

```bash
# Install dependencies
npm install

# Run all integration tests
npm test

# Run specific test suites
npm run test:api-gateway
npm run test:database
npm run test:data-bridge
npm run test:central-hub
npm run test:workspace

# Run only critical tests
npm run test:critical

# Quick validation (key services only)
npm run test:quick
```

## Test Suites

### 1. API Gateway Tests (`api-gateway.test.js`)
- Service connectivity on port 3001
- Health endpoint validation
- Authentication system readiness
- Central Hub integration configuration
- Security middleware (CORS, security headers)
- Error handling (404, validation)
- Performance benchmarks

### 2. Database Service Tests (`database-service.test.js`)
- Multi-database connections (5 databases):
  - `aitrading_main` - Core application data
  - `aitrading_auth` - Authentication and user management
  - `aitrading_trading` - Trading operations and positions
  - `aitrading_market` - Market data and analysis
  - `aitrading_analytics` - Analytics and reporting
- Database service API endpoints
- Query interface functionality
- Migration system
- Performance testing

### 3. Data Bridge Tests (`data-bridge.test.js`)
- Service startup and health
- MT5 connection status reporting
- REST API endpoints (status, symbols, market data)
- WebSocket server connectivity
- Real-time data flow (ping/pong)
- Error handling
- Performance benchmarks

### 4. Central Hub Tests (`central-hub.test.js`)
- Service discovery functionality
- Service registration API
- Health monitoring capabilities
- Foundation service detection
- Registry integration
- Performance testing

### 5. Workspace Configuration Tests (`workspace-config.test.js`)
- Configuration file validation
- Environment variable setup
- Service URL configuration
- Dependency configuration
- Integration readiness assessment

## Test Configuration

The test configuration (`config/test-config.js`) includes:

- Service endpoints and ports
- Database connection parameters
- Performance thresholds
- Test data and credentials
- Integration flow configuration

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