// MT5 Performance Testing Suite - Main Export File

// Infrastructure and base classes
export { PerformanceTestBase, PerformanceTestRunner } from './infrastructure/PerformanceTestBase';
export { MT5TestHelper, MT5ConnectionPool } from './infrastructure/MT5TestHelper';

// Individual test classes
export { MT5LatencyTest } from './latency/MT5LatencyTest';
export { MT5ThroughputTest } from './throughput/MT5ThroughputTest';
export { MT5StressTest } from './stress/MT5StressTest';
export { MT5MemoryTest } from './memory/MT5MemoryTest';
export { MT5LoadTest } from './load/MT5LoadTest';
export { MT5BenchmarkSuite } from './benchmarks/MT5BenchmarkSuite';
export { MT5DataFeedTest } from './datafeed/MT5DataFeedTest';
export { MT5StabilityTest } from './stability/MT5StabilityTest';

// Main test suite and coordination
export { MT5PerformanceTestSuite } from './MT5PerformanceTestSuite';
export { HooksIntegration, PerformanceTestCoordinator, createHooksIntegration } from './utils/HooksIntegration';

// Type definitions
export type {
  PerformanceMetrics,
  TestConfig
} from './infrastructure/PerformanceTestBase';

export type {
  MT5ConnectionConfig,
  MT5OrderRequest,
  MT5TickData
} from './infrastructure/MT5TestHelper';

export type {
  MT5PerformanceTestConfig,
  TestSuite,
  PerformanceThresholds,
  TestResults,
  TestSummary,
  ThresholdViolation
} from './MT5PerformanceTestSuite';

// Utility functions for quick test setup
export function createQuickLatencyTest(mt5Config: any, options?: any) {
  return new MT5LatencyTest(mt5Config, {
    duration: 300000, // 5 minutes
    iterations: 100,
    ...options
  });
}

export function createQuickThroughputTest(mt5Config: any, options?: any) {
  return new MT5ThroughputTest(mt5Config, {
    duration: 600000, // 10 minutes
    concurrency: 20,
    ...options
  });
}

export function createQuickStressTest(mt5Config: any, options?: any) {
  return new MT5StressTest(mt5Config, {
    duration: 1800000, // 30 minutes
    maxConnections: 50,
    ...options
  });
}

export function createQuickMemoryTest(mt5Config: any, options?: any) {
  return new MT5MemoryTest(mt5Config, {
    duration: 900000, // 15 minutes
    memoryMonitoringInterval: 5000,
    ...options
  });
}

// Pre-configured test suites for common scenarios
export const TRADING_PERFORMANCE_SUITE: MT5PerformanceTestConfig = {
  mt5Config: {
    server: 'demo-server',
    login: 12345,
    password: 'password',
    timeout: 30000,
    retries: 3
  },
  enabledTests: [
    {
      name: 'latency',
      enabled: true,
      priority: 'high',
      tags: ['trading', 'real-time'],
      config: {
        duration: 300000,
        orderTestCount: 100,
        tickDataTestCount: 500
      }
    },
    {
      name: 'throughput',
      enabled: true,
      priority: 'high',
      tags: ['trading', 'volume'],
      config: {
        duration: 600000,
        concurrentConnections: 10,
        testPatterns: ['orders', 'ticks', 'mixed']
      }
    },
    {
      name: 'stability',
      enabled: true,
      priority: 'high',
      tags: ['reliability'],
      config: {
        duration: 1800000,
        connectionResilience: {
          forcedDisconnections: 5,
          reconnectionTimeout: 30000
        }
      }
    }
  ],
  coordination: {
    enabled: true,
    teamMemoryStorage: true,
    realTimeReporting: true
  },
  reporting: {
    generateReports: true,
    exportResults: true,
    compareBaseline: false,
    outputFormats: ['json', 'markdown']
  },
  thresholds: {
    latency: {
      p95: 100, // 100ms
      p99: 200,
      average: 50
    },
    throughput: {
      minimum: 100, // 100 req/s
      target: 200
    },
    memory: {
      maxUsage: 512, // 512MB
      leakThreshold: 10 // 10MB/min
    },
    stability: {
      minUptime: 99.5, // 99.5%
      maxErrorRate: 1 // 1%
    },
    stress: {
      maxLatencyDegradation: 50, // 50%
      minStabilityUnderLoad: 95 // 95%
    }
  }
};

export const COMPREHENSIVE_PERFORMANCE_SUITE: MT5PerformanceTestConfig = {
  ...TRADING_PERFORMANCE_SUITE,
  enabledTests: [
    ...TRADING_PERFORMANCE_SUITE.enabledTests,
    {
      name: 'memory',
      enabled: true,
      priority: 'medium',
      tags: ['memory', 'leak-detection'],
      config: {
        duration: 900000,
        leakDetectionThreshold: 20
      }
    },
    {
      name: 'load',
      enabled: true,
      priority: 'medium',
      tags: ['scalability'],
      config: {
        duration: 1800000,
        maxConcurrentUsers: 100
      }
    },
    {
      name: 'benchmark',
      enabled: true,
      priority: 'low',
      tags: ['benchmarking'],
      config: {
        iterations: 1000,
        warmupIterations: 100
      }
    },
    {
      name: 'datafeed',
      enabled: true,
      priority: 'medium',
      tags: ['data-processing'],
      config: {
        duration: 1200000,
        symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD']
      }
    }
  ]
};

export const STRESS_TEST_SUITE: MT5PerformanceTestConfig = {
  ...TRADING_PERFORMANCE_SUITE,
  enabledTests: [
    {
      name: 'stress',
      enabled: true,
      priority: 'high',
      tags: ['stress', 'high-frequency'],
      config: {
        duration: 3600000, // 1 hour
        maxConnections: 200,
        orderVelocity: 10,
        tickDataVelocity: 20,
        highFrequencyBursts: {
          enabled: true,
          burstSize: 100,
          burstFrequency: 6,
          maxConcurrentBursts: 5
        }
      }
    },
    {
      name: 'memory',
      enabled: true,
      priority: 'high',
      tags: ['memory', 'stress'],
      config: {
        duration: 3600000,
        leakDetectionThreshold: 5, // Stricter threshold
        maxHeapGrowth: 1000
      }
    },
    {
      name: 'stability',
      enabled: true,
      priority: 'high',
      tags: ['reliability', 'stress'],
      config: {
        duration: 7200000, // 2 hours
        longRunningTest: {
          enabled: true,
          duration: 7200000,
          degradationThreshold: 10
        }
      }
    }
  ],
  thresholds: {
    ...TRADING_PERFORMANCE_SUITE.thresholds,
    latency: {
      p95: 200, // More lenient under stress
      p99: 500,
      average: 100
    },
    memory: {
      maxUsage: 2048, // 2GB for stress testing
      leakThreshold: 5 // Stricter leak detection
    }
  }
};

// Quick execution functions
export async function runTradingPerformanceTest(mt5Config: any): Promise<TestResults> {
  const suite = new MT5PerformanceTestSuite({
    ...TRADING_PERFORMANCE_SUITE,
    mt5Config
  });

  return await suite.runAllTests();
}

export async function runComprehensivePerformanceTest(mt5Config: any): Promise<TestResults> {
  const suite = new MT5PerformanceTestSuite({
    ...COMPREHENSIVE_PERFORMANCE_SUITE,
    mt5Config
  });

  return await suite.runAllTests();
}

export async function runStressTest(mt5Config: any): Promise<TestResults> {
  const suite = new MT5PerformanceTestSuite({
    ...STRESS_TEST_SUITE,
    mt5Config
  });

  return await suite.runAllTests();
}

// Example usage and documentation
export const EXAMPLE_USAGE = `
// Quick test execution
import { runTradingPerformanceTest } from './tests/performance';

const mt5Config = {
  server: 'your-mt5-server',
  login: 12345,
  password: 'your-password',
  timeout: 30000,
  retries: 3
};

const results = await runTradingPerformanceTest(mt5Config);
console.log(\`Overall Grade: \${results.summary.grade}\`);

// Custom test suite
import { MT5PerformanceTestSuite } from './tests/performance';

const customSuite = new MT5PerformanceTestSuite({
  mt5Config,
  enabledTests: [
    { name: 'latency', enabled: true, priority: 'high', tags: ['real-time'] }
  ],
  coordination: { enabled: true, teamMemoryStorage: true },
  thresholds: { latency: { p95: 50 } }
});

const customResults = await customSuite.runAllTests();
`;

export default {
  MT5PerformanceTestSuite,
  TRADING_PERFORMANCE_SUITE,
  COMPREHENSIVE_PERFORMANCE_SUITE,
  STRESS_TEST_SUITE,
  runTradingPerformanceTest,
  runComprehensivePerformanceTest,
  runStressTest
};