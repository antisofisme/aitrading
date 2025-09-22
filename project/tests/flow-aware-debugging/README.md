# Flow-Aware Error Handling Test Suite

A comprehensive test suite for validating the Flow-Aware Error Handling system across all components and integration scenarios. This test suite ensures production readiness, reliability, and performance of the error handling and debugging infrastructure.

## 🎯 Test Coverage

### Test Categories

- **Unit Tests** - Individual component testing (FlowRegistry, ChainHealthMonitor, ChainImpactAnalyzer)
- **Integration Tests** - Cross-service flow tracking and error propagation
- **End-to-End Tests** - Complete debugging scenarios and workflows
- **Performance Tests** - Scalability, throughput, and resource efficiency
- **Chaos Tests** - Failure injection and recovery validation
- **Production Readiness** - SLA compliance and production deployment validation

### Coverage Metrics

- **Lines**: >90% coverage target
- **Functions**: >95% coverage target
- **Branches**: >85% coverage target
- **Statements**: >90% coverage target

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm 8+
- 8GB+ RAM recommended for full test suite
- Docker (optional, for integration tests)

### Installation

```bash
cd tests/flow-aware-debugging
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run specific test categories
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests only
npm run test:e2e          # End-to-end tests only
npm run test:performance  # Performance tests only
npm run test:chaos        # Chaos engineering tests
npm run test:production   # Production readiness tests

# Development workflows
npm run test:watch        # Watch mode for development
npm run test:coverage     # Generate coverage report
npm run test:verbose      # Detailed test output
npm run test:debug        # Debug mode with inspector
```

## 📊 Test Scenarios

### Unit Testing Scenarios

#### FlowRegistry Tests
- ✅ High-frequency flow registration (10K+ flows/minute)
- ✅ Concurrent flow operations and data consistency
- ✅ Query performance with large datasets (50K+ flows)
- ✅ Memory management and garbage collection
- ✅ Error handling and recovery

#### ChainHealthMonitor Tests
- ✅ Multi-service health monitoring (100+ services)
- ✅ Circuit breaker patterns and failover
- ✅ Alert generation and escalation
- ✅ Health aggregation and reporting
- ✅ Performance degradation detection

#### ChainImpactAnalyzer Tests
- ✅ Root cause detection algorithms
- ✅ Cascading failure analysis
- ✅ Business impact calculation
- ✅ ML-based pattern recognition
- ✅ Recovery strategy optimization

### Integration Testing Scenarios

- ✅ Cross-service flow tracking with realistic topology
- ✅ Error propagation through service dependencies
- ✅ Circuit breaker coordination across services
- ✅ Real-time monitoring and alerting
- ✅ Data consistency during failures

### End-to-End Testing Scenarios

- ✅ High-frequency trading latency spike investigation
- ✅ Market volatility cascade failure handling
- ✅ Distributed transaction rollback scenarios
- ✅ Security incident detection and response
- ✅ Multi-region consistency issues

### Performance Testing Scenarios

- ✅ 10,000 flows/minute sustained throughput
- ✅ Sub-second response times under load
- ✅ Memory usage optimization (< 2KB per flow)
- ✅ Concurrent operation scaling
- ✅ Database query optimization

### Chaos Testing Scenarios

- ✅ Service crash and automatic recovery
- ✅ Network partitions and split-brain scenarios
- ✅ Resource exhaustion (memory, CPU, disk)
- ✅ Cascading failure isolation
- ✅ Data consistency during chaos events

### Production Readiness Tests

- ✅ 99.9% uptime requirement validation
- ✅ SLA compliance under load (P95 < 1s)
- ✅ Security and compliance validation
- ✅ Horizontal scaling patterns
- ✅ Monitoring and observability requirements

## 🔧 Configuration

### Environment Variables

```bash
# Test Environment
NODE_ENV=test
LOG_LEVEL=error
METRICS_ENABLED=true
CHAOS_TESTING=enabled

# Performance Tuning
NODE_OPTIONS=--max-old-space-size=8192 --expose-gc
TEST_TIMEOUT=120000
JEST_WORKERS=50%

# External Dependencies
REDIS_URL=redis://localhost:6379
MOCK_EXTERNAL_SERVICES=true
```

### Test Configuration Files

- `jest.config.js` - Main Jest configuration
- `setup/jest.setup.js` - Global test utilities and matchers
- `setup/mocks.setup.js` - Mock implementations
- `setup/global.setup.js` - Global test environment setup
- `setup/global.teardown.js` - Cleanup and reporting

## 📈 Performance Benchmarks

### Baseline Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Flow Registration | < 50ms P95 | 10ms P50, 50ms P95, 100ms P99 |
| Health Check Latency | < 20ms P95 | 5ms P50, 20ms P95, 50ms P99 |
| Impact Analysis | < 500ms P95 | 100ms P50, 500ms P95, 1s P99 |
| Query Response | < 100ms P95 | 20ms P50, 100ms P95, 200ms P99 |
| Memory per Flow | < 2KB | Typical 1KB, max 2KB |
| Throughput | > 1000 flows/sec | Target 1000, stretch 5000 |

### Scalability Targets

- **Concurrent Users**: 10,000+ simultaneous connections
- **Flow Volume**: 10,000+ flows/minute sustained
- **Service Monitoring**: 1,000+ services simultaneously
- **Error Analysis**: 100+ concurrent analyses
- **Memory Usage**: < 512MB total for 100K flows

## 🧪 Test Data

### Mock Data Generation

The test suite includes comprehensive mock data generators:

- **Flow Data**: Realistic trading flows with metadata
- **Service Health**: Varied health states and dependencies
- **Error Scenarios**: Production-like error patterns
- **Performance Data**: Load patterns and stress scenarios
- **Chaos Events**: Failure injection scenarios

### Test Environments

- **Local Development**: Lightweight mocks
- **CI/CD Pipeline**: Full integration testing
- **Performance Lab**: High-resource testing
- **Chaos Lab**: Failure injection testing

## 🔍 Debugging and Troubleshooting

### Common Issues

#### Memory Issues
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=8192"

# Enable garbage collection logging
export NODE_OPTIONS="--max-old-space-size=8192 --expose-gc"
```

#### Timeout Issues
```bash
# Increase test timeout
npm run test:performance -- --testTimeout=300000

# Run with fewer workers
npm run test -- --maxWorkers=2
```

#### Mock Issues
```bash
# Clear Jest cache
npm run clean
npx jest --clearCache

# Run with verbose mocking
npm run test:verbose -- --verbose
```

### Debug Mode

```bash
# Run specific test in debug mode
npm run test:debug -- --testNamePattern="should handle cascading failures"

# Debug with Chrome DevTools
node --inspect-brk node_modules/.bin/jest --runInBand
```

## 📋 CI/CD Integration

### GitHub Actions Workflow

The test suite includes a comprehensive GitHub Actions workflow:

- **Matrix Testing**: Parallel execution across multiple shards
- **Service Dependencies**: Automatic Redis/database setup
- **Artifact Collection**: Test results and coverage reports
- **Quality Gates**: Coverage and performance thresholds
- **Notifications**: Slack integration for scheduled runs

### Pipeline Stages

1. **Setup and Validation** - Dependency installation and linting
2. **Unit Tests** - Parallel execution with sharding
3. **Integration Tests** - Service dependency testing
4. **E2E Tests** - Complete scenario validation
5. **Performance Tests** - Scalability and performance validation
6. **Chaos Tests** - Failure injection and recovery
7. **Production Tests** - Production readiness validation
8. **Coverage Report** - Merged coverage analysis
9. **Quality Gates** - Threshold validation and reporting

### Quality Gates

- **Coverage**: Lines >85%, Functions >90%, Branches >80%
- **Performance**: All benchmarks within SLA targets
- **Reliability**: 99.9% uptime requirement validation
- **Security**: No sensitive data leakage in logs

## 🎛️ Monitoring and Observability

### Test Metrics

The test suite automatically generates metrics for:

- **Execution Time**: Per test category and individual tests
- **Memory Usage**: Peak memory and garbage collection
- **Error Rates**: Test failures and error patterns
- **Coverage**: Code coverage across all categories
- **Performance**: Benchmark results and trends

### Dashboards

Test results are available through:

- **HTML Reports**: Comprehensive test result visualization
- **Coverage Reports**: Interactive coverage exploration
- **Performance Reports**: Benchmark trend analysis
- **Chaos Reports**: Failure injection result analysis

## 🤝 Contributing

### Running Tests During Development

```bash
# Quick feedback loop
npm run test:unit -- --watch

# Test specific component
npm run test:unit -- --testPathPattern="flow-registry"

# Coverage for specific files
npm run test:coverage -- --collectCoverageFrom="**/flow-registry.js"
```

### Adding New Tests

1. **Unit Tests**: Add to `unit/` directory with `.test.js` suffix
2. **Integration Tests**: Add to `integration/` directory
3. **Mock Components**: Add to `mocks/` directory
4. **Test Utilities**: Add to `utils/` directory

### Test Naming Conventions

- Use descriptive test names that explain the scenario
- Group related tests with `describe()` blocks
- Use `it()` for individual test cases
- Include expected behavior in test names

```javascript
describe('FlowRegistry Performance', () => {
  it('should handle 10,000 concurrent flow registrations within 5 seconds', async () => {
    // Test implementation
  });
});
```

## 📚 Additional Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Flow-Aware Error Handling Architecture](../docs/architecture.md)
- [Performance Benchmarking Guide](../docs/performance.md)
- [Chaos Engineering Principles](../docs/chaos-engineering.md)

## 🆘 Support

For questions or issues with the test suite:

1. Check the [Troubleshooting](#debugging-and-troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with:
   - Test command that failed
   - Error output
   - Environment details (Node.js version, OS, etc.)
   - Steps to reproduce

---

**Happy Testing! 🧪✨**