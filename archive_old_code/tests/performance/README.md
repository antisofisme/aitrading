# MT5 Performance Testing Suite

A comprehensive performance testing framework for MetaTrader 5 (MT5) integration, designed for high-frequency trading environments with real-time monitoring, team coordination, and automated reporting.

## 🚀 Features

### Core Testing Capabilities
- **Latency Testing**: Measure API call latency, order execution speed, and data retrieval performance
- **Throughput Testing**: High-volume trade processing and concurrent connection handling
- **Stress Testing**: High-frequency trading scenarios with burst pattern simulation
- **Memory Testing**: Memory usage monitoring, leak detection, and resource management
- **Load Testing**: Concurrent user simulation with realistic trading patterns
- **Stability Testing**: Connection resilience, error recovery, and long-running reliability
- **Data Feed Testing**: Real-time tick processing, buffer management, and quality assessment
- **Benchmark Suite**: Performance benchmarking with statistical analysis

### Advanced Features
- **Team Coordination**: Claude-Flow hooks integration for team memory storage
- **Real-time Monitoring**: Live performance metrics and threshold monitoring
- **Automated Reporting**: Comprehensive reports in multiple formats (JSON, Markdown, HTML)
- **Threshold Management**: Configurable performance thresholds with violation detection
- **Baseline Comparison**: Compare results against historical baselines
- **HFT Analysis**: Specialized analysis for high-frequency trading suitability

## 📊 Quick Start

### Installation

```bash
# Install dependencies
npm install

# Ensure Claude-Flow is available for hooks integration
npm install -g claude-flow@alpha
```

### Basic Usage

```typescript
import { runTradingPerformanceTest } from './tests/performance';

const mt5Config = {
  server: 'your-mt5-server',
  login: 12345,
  password: 'your-password',
  timeout: 30000,
  retries: 3
};

// Run quick trading performance test
const results = await runTradingPerformanceTest(mt5Config);
console.log(`Overall Grade: ${results.summary.grade}`);
console.log(`Performance Score: ${results.summary.overallScore}/100`);
```

### CLI Usage

```bash
# Run all performance tests
npm run test:performance

# Run specific test suites
npm run test:performance:trading     # Quick trading test
npm run test:performance:comprehensive  # Full test suite
npm run test:performance:stress      # Stress testing
npm run test:performance:hft         # High-frequency trading test

# Run with custom configuration
npx ts-node tests/performance/examples/RunPerformanceTests.ts trading
```

## 🧪 Test Suites

### 1. Trading Performance Suite (5-10 minutes)
```typescript
import { TRADING_PERFORMANCE_SUITE } from './tests/performance';
```
- Latency testing (order execution, tick retrieval)
- Throughput testing (concurrent operations)
- Stability testing (connection resilience)
- **Recommended for**: Production readiness validation

### 2. Comprehensive Performance Suite (20-30 minutes)
```typescript
import { COMPREHENSIVE_PERFORMANCE_SUITE } from './tests/performance';
```
- All trading tests plus:
- Memory leak detection
- Load testing with multiple user scenarios
- Data feed processing validation
- Benchmark comparisons
- **Recommended for**: Full system validation

### 3. Stress Test Suite (30-60 minutes)
```typescript
import { STRESS_TEST_SUITE } from './tests/performance';
```
- High-frequency trading simulation
- Extended memory stress testing
- Connection drop and recovery testing
- Performance degradation analysis
- **Recommended for**: HFT system validation

## 📈 Performance Metrics

### Latency Metrics
- **P50, P95, P99 percentiles** - Response time distribution
- **Min/Max/Average** - Overall latency characteristics
- **Standard deviation** - Consistency measurement
- **Operation-specific latency** - Per API call analysis

### Throughput Metrics
- **Requests per second** - Overall system throughput
- **Concurrent connection handling** - Scalability measurement
- **Pattern-specific throughput** - Per operation type analysis
- **Burst handling capacity** - Peak load performance

### Memory Metrics
- **Heap usage tracking** - Memory consumption monitoring
- **Leak detection** - Growth rate analysis
- **Garbage collection impact** - Memory efficiency
- **Buffer overflow detection** - Resource management

### Stability Metrics
- **Uptime percentage** - System availability
- **Connection drop rate** - Network resilience
- **Error recovery time** - Fault tolerance
- **MTBF/MTTR** - Reliability indicators

## 🔧 Configuration

### MT5 Configuration
```typescript
const mt5Config = {
  server: 'demo-server',      // MT5 server address
  login: 12345,               // Account login
  password: 'password',       // Account password
  timeout: 30000,             // Connection timeout (ms)
  retries: 3                  // Retry attempts
};
```

### Performance Thresholds
```typescript
const thresholds = {
  latency: {
    p95: 100,        // 100ms P95 latency
    p99: 200,        // 200ms P99 latency
    average: 50      // 50ms average latency
  },
  throughput: {
    minimum: 100,    // 100 req/s minimum
    target: 200      // 200 req/s target
  },
  memory: {
    maxUsage: 512,   // 512MB max usage
    leakThreshold: 10 // 10MB/min leak threshold
  },
  stability: {
    minUptime: 99.5,    // 99.5% uptime requirement
    maxErrorRate: 1     // 1% max error rate
  }
};
```

### Team Coordination
```typescript
const coordination = {
  enabled: true,              // Enable team coordination
  teamMemoryStorage: true,    // Store results in team memory
  realTimeReporting: true,    // Real-time metrics updates
  slackNotifications: false   // Slack notifications (optional)
};
```

## 📊 Example Results

### Performance Grade System
- **Grade A (90-100)**: Excellent performance, production ready
- **Grade B (80-89)**: Good performance, minor optimizations recommended
- **Grade C (70-79)**: Acceptable performance, improvements needed
- **Grade D (60-69)**: Poor performance, significant optimization required
- **Grade F (<60)**: Unacceptable performance, major issues

### Sample Output
```
🎉 MT5 Performance Test Suite Results
=====================================
Overall Grade: A (94.2/100)
Total Tests: 8
Passed: 8/8 (100%)
Duration: 23.4 minutes

Test Results:
✅ Latency Test: P95=42ms, Avg=18ms
✅ Throughput Test: 347 req/s
✅ Memory Test: 234MB peak, no leaks
✅ Stability Test: 99.8% uptime
```

## 🔗 Hooks Integration

The test suite integrates with Claude-Flow hooks for team coordination:

### Pre-Task Hook
```bash
npx claude-flow@alpha hooks pre-task --description "MT5 Performance Testing"
```

### Memory Storage
```bash
npx claude-flow@alpha hooks post-edit --memory-key "performance/results" --value "{results}"
```

### Team Notifications
```bash
npx claude-flow@alpha hooks notify --message "Performance test completed with grade A"
```

### Session Management
```bash
npx claude-flow@alpha hooks session-restore --session-id "perf_test_session"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🚀 Advanced Usage

### Custom Test Configuration
```typescript
import { MT5PerformanceTestSuite } from './tests/performance';

const customConfig = {
  mt5Config,
  enabledTests: [
    {
      name: 'latency',
      enabled: true,
      priority: 'high',
      tags: ['real-time', 'trading'],
      config: {
        duration: 300000,
        orderTestCount: 500,
        tickDataTestCount: 1000
      }
    }
  ],
  thresholds: {
    latency: { p95: 50 }, // Stricter requirements
    // ... other thresholds
  }
};

const suite = new MT5PerformanceTestSuite(customConfig);
const results = await suite.runAllTests();
```

### Individual Test Execution
```typescript
import { MT5LatencyTest, MT5ThroughputTest } from './tests/performance';

// Run only latency test
const latencyTest = new MT5LatencyTest(mt5Config, {
  duration: 300000,
  iterations: 1000
});
const latencyResults = await latencyTest.run();

// Run only throughput test
const throughputTest = new MT5ThroughputTest(mt5Config, {
  concurrentConnections: 20,
  testPatterns: ['orders', 'ticks', 'mixed']
});
const throughputResults = await throughputTest.run();
```

### High-Frequency Trading Validation
```typescript
import { runStressTest } from './tests/performance';

// Validate HFT performance with strict thresholds
const hftResults = await runStressTest({
  ...mt5Config,
  thresholds: {
    latency: { p95: 25 },      // Ultra-low latency requirement
    throughput: { minimum: 1000 }, // High throughput requirement
    stability: { minUptime: 99.9 }  // High availability requirement
  }
});

console.log(`HFT Suitable: ${hftResults.summary.grade >= 'B'}`);
```

## 📁 Project Structure

```
tests/performance/
├── infrastructure/
│   ├── PerformanceTestBase.ts     # Base test framework
│   └── MT5TestHelper.ts           # MT5 integration utilities
├── latency/
│   └── MT5LatencyTest.ts          # Latency testing
├── throughput/
│   └── MT5ThroughputTest.ts       # Throughput testing
├── stress/
│   └── MT5StressTest.ts           # Stress testing
├── memory/
│   └── MT5MemoryTest.ts           # Memory testing
├── load/
│   └── MT5LoadTest.ts             # Load testing
├── benchmarks/
│   └── MT5BenchmarkSuite.ts       # Benchmark testing
├── datafeed/
│   └── MT5DataFeedTest.ts         # Data feed testing
├── stability/
│   └── MT5StabilityTest.ts        # Stability testing
├── utils/
│   └── HooksIntegration.ts        # Team coordination
├── examples/
│   └── RunPerformanceTests.ts     # Usage examples
├── MT5PerformanceTestSuite.ts     # Main test suite
├── index.ts                       # Exports and utilities
└── README.md                      # This file
```

## 🎯 Use Cases

### Development Validation
- Validate performance before deployment
- Catch performance regressions early
- Ensure consistency across environments

### Production Monitoring
- Continuous performance monitoring
- SLA compliance validation
- Capacity planning insights

### High-Frequency Trading
- Ultra-low latency validation
- Throughput scalability testing
- System stability under extreme load

### Team Coordination
- Shared performance metrics
- Collaborative analysis
- Automated reporting and alerts

## 🔍 Troubleshooting

### Common Issues

**High Latency Results**
- Check network connectivity to MT5 server
- Verify MT5 server performance
- Review connection pooling configuration

**Memory Leaks Detected**
- Check object disposal in MT5 operations
- Review connection cleanup procedures
- Monitor garbage collection frequency

**Connection Failures**
- Verify MT5 credentials and server settings
- Check firewall and network configuration
- Review connection timeout settings

**Threshold Violations**
- Adjust thresholds based on environment
- Investigate specific test failures
- Review system resource allocation

### Performance Optimization Tips

1. **Connection Management**
   - Use connection pooling
   - Implement keep-alive mechanisms
   - Optimize connection timeout settings

2. **Memory Management**
   - Implement proper object disposal
   - Use efficient data structures
   - Monitor garbage collection impact

3. **Network Optimization**
   - Minimize network round trips
   - Implement request batching
   - Use connection compression

4. **Error Handling**
   - Implement retry mechanisms
   - Use circuit breaker patterns
   - Monitor error rates and patterns

## 🤝 Contributing

1. **Adding New Tests**
   - Extend `PerformanceTestBase` class
   - Implement test-specific logic
   - Add to test suite configuration

2. **Improving Metrics**
   - Add new performance indicators
   - Enhance statistical analysis
   - Implement comparative benchmarking

3. **Integration Enhancement**
   - Extend hooks integration
   - Add new coordination features
   - Improve team collaboration tools

## 📄 License

This performance testing suite is part of the aitrading project and follows the same license terms.

---

**Note**: This testing suite simulates MT5 operations for demonstration purposes. In production, replace the `MT5TestHelper` simulation methods with actual MT5 API calls for realistic performance measurement.