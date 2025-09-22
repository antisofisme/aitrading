/**
 * Jest Setup Configuration for Flow-Aware Error Handling Tests
 * Provides global test utilities, mocks, and environment setup
 */

const { TextEncoder, TextDecoder } = require('util');

// Polyfills for Node.js environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Extended timeout for complex tests
jest.setTimeout(120000);

// Global test utilities
global.testUtils = {
  // Generate test data
  generateFlowId: () => `flow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  generateServiceId: () => `service_${Math.random().toString(36).substr(2, 8)}`,
  generateChainId: () => `chain_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
  generateErrorId: () => `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,

  // Create mock objects
  createMockError: (overrides = {}) => ({
    id: global.testUtils.generateErrorId(),
    serviceId: 'test-service',
    type: 'test_error',
    severity: 'medium',
    message: 'Test error message',
    timestamp: Date.now(),
    stack: 'Test stack trace',
    metadata: {},
    ...overrides
  }),

  createMockService: (overrides = {}) => ({
    id: global.testUtils.generateServiceId(),
    name: 'Test Service',
    healthEndpoint: 'http://localhost:3000/health',
    dependencies: [],
    criticality: 'medium',
    status: 'healthy',
    ...overrides
  }),

  createMockFlow: (overrides = {}) => ({
    id: global.testUtils.generateFlowId(),
    serviceId: 'test-service',
    status: 'pending',
    timestamp: Date.now(),
    metadata: {},
    steps: [],
    errors: [],
    ...overrides
  }),

  // Timing utilities
  waitForCondition: async (condition, timeout = 10000, interval = 100) => {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error(`Condition not met within ${timeout}ms`);
  },

  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // Performance measurement
  measurePerformance: async (fn, iterations = 1) => {
    const times = [];

    for (let i = 0; i < iterations; i++) {
      const start = Date.now();
      await fn();
      times.push(Date.now() - start);
    }

    return {
      min: Math.min(...times),
      max: Math.max(...times),
      avg: times.reduce((a, b) => a + b, 0) / times.length,
      total: times.reduce((a, b) => a + b, 0),
      times
    };
  },

  // Memory utilities
  getMemoryUsage: () => {
    const usage = process.memoryUsage();
    return {
      heapUsed: Math.round(usage.heapUsed / 1024 / 1024), // MB
      heapTotal: Math.round(usage.heapTotal / 1024 / 1024), // MB
      external: Math.round(usage.external / 1024 / 1024), // MB
      rss: Math.round(usage.rss / 1024 / 1024) // MB
    };
  },

  forceGarbageCollection: () => {
    if (global.gc) {
      global.gc();
    }
  },

  // Mock data generators
  generateRandomData: (size) => {
    return Array.from({ length: size }, (_, i) => ({
      id: i,
      value: Math.random() * 1000,
      timestamp: Date.now() - (Math.random() * 86400000), // Random within 24h
      category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)]
    }));
  },

  generateLoadPattern: (options = {}) => {
    const {
      duration = 60000, // 1 minute
      peakRPS = 100,
      pattern = 'constant' // constant, ramp-up, spike, wave
    } = options;

    const points = [];
    const interval = 1000; // 1 second intervals
    const totalPoints = duration / interval;

    for (let i = 0; i < totalPoints; i++) {
      const time = i * interval;
      let rps;

      switch (pattern) {
        case 'ramp-up':
          rps = (i / totalPoints) * peakRPS;
          break;
        case 'spike':
          rps = i === Math.floor(totalPoints / 2) ? peakRPS : peakRPS * 0.1;
          break;
        case 'wave':
          rps = peakRPS * (0.5 + 0.5 * Math.sin(2 * Math.PI * i / totalPoints));
          break;
        default: // constant
          rps = peakRPS;
      }

      points.push({ time, rps });
    }

    return points;
  }
};

// Global test configuration
global.testConfig = {
  // Default timeouts
  DEFAULT_TIMEOUT: 30000,
  LONG_TIMEOUT: 120000,
  SHORT_TIMEOUT: 5000,

  // Performance thresholds
  PERFORMANCE_THRESHOLDS: {
    FLOW_REGISTRATION: 50, // ms
    QUERY_RESPONSE: 100, // ms
    HEALTH_CHECK: 20, // ms
    IMPACT_ANALYSIS: 500, // ms
    MEMORY_PER_FLOW: 2048, // bytes
    ERROR_RATE: 0.001 // 0.1%
  },

  // Test data limits
  TEST_LIMITS: {
    MAX_FLOWS: 10000,
    MAX_SERVICES: 100,
    MAX_ERRORS: 1000,
    BATCH_SIZE: 100
  },

  // Mock service endpoints
  MOCK_ENDPOINTS: {
    HEALTH: '/health',
    METRICS: '/metrics',
    STATUS: '/status'
  }
};

// Global mock factories
global.mockFactories = {
  createMockLogger: () => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
    trace: jest.fn()
  }),

  createMockMetrics: () => ({
    increment: jest.fn(),
    gauge: jest.fn(),
    histogram: jest.fn(),
    timer: jest.fn(),
    summary: jest.fn()
  }),

  createMockCache: () => {
    const cache = new Map();
    return {
      get: jest.fn((key) => cache.get(key)),
      set: jest.fn((key, value, ttl) => cache.set(key, value)),
      delete: jest.fn((key) => cache.delete(key)),
      clear: jest.fn(() => cache.clear()),
      size: () => cache.size,
      has: jest.fn((key) => cache.has(key))
    };
  },

  createMockDatabase: () => ({
    connect: jest.fn().mockResolvedValue(true),
    disconnect: jest.fn().mockResolvedValue(true),
    query: jest.fn().mockResolvedValue([]),
    insert: jest.fn().mockResolvedValue({ id: 1 }),
    update: jest.fn().mockResolvedValue({ affected: 1 }),
    delete: jest.fn().mockResolvedValue({ affected: 1 }),
    transaction: jest.fn().mockImplementation(async (fn) => {
      const tx = {
        query: jest.fn().mockResolvedValue([]),
        commit: jest.fn().mockResolvedValue(true),
        rollback: jest.fn().mockResolvedValue(true)
      };
      return fn(tx);
    })
  }),

  createMockEventEmitter: () => {
    const events = new Map();
    return {
      on: jest.fn((event, listener) => {
        if (!events.has(event)) events.set(event, []);
        events.get(event).push(listener);
      }),
      off: jest.fn((event, listener) => {
        if (events.has(event)) {
          const listeners = events.get(event);
          const index = listeners.indexOf(listener);
          if (index > -1) listeners.splice(index, 1);
        }
      }),
      emit: jest.fn((event, ...args) => {
        if (events.has(event)) {
          events.get(event).forEach(listener => listener(...args));
        }
      }),
      removeAllListeners: jest.fn((event) => {
        if (event) {
          events.delete(event);
        } else {
          events.clear();
        }
      })
    };
  }
};

// Custom Jest matchers
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false
      };
    }
  },

  toHavePerformanceWithin(received, threshold) {
    const pass = received.avg <= threshold;
    if (pass) {
      return {
        message: () => `expected average performance ${received.avg}ms not to be within threshold ${threshold}ms`,
        pass: true
      };
    } else {
      return {
        message: () => `expected average performance ${received.avg}ms to be within threshold ${threshold}ms`,
        pass: false
      };
    }
  },

  toBeHealthy(received) {
    const isHealthy = received.status === 'healthy' || received.status === 'ok';
    if (isHealthy) {
      return {
        message: () => `expected ${received.status} not to be healthy`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received.status} to be healthy`,
        pass: false
      };
    }
  }
});

// Cleanup function for tests
global.testCleanup = {
  clearAllMocks: () => {
    jest.clearAllMocks();
  },

  resetAllMocks: () => {
    jest.resetAllMocks();
  },

  restoreAllMocks: () => {
    jest.restoreAllMocks();
  },

  cleanupMemory: () => {
    if (global.gc) {
      global.gc();
    }
  }
};

// Error handling for unhandled promises
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Console output filtering for cleaner test output
const originalConsoleError = console.error;
console.error = (...args) => {
  // Filter out known harmless warnings
  const message = args.join(' ');
  const ignoredMessages = [
    'Warning: React.createFactory() is deprecated',
    'Warning: componentWillMount has been renamed'
  ];

  if (!ignoredMessages.some(ignored => message.includes(ignored))) {
    originalConsoleError.apply(console, args);
  }
};

// Test environment validation
const validateTestEnvironment = () => {
  const required = ['Node.js', 'Jest'];
  const nodeVersion = process.version;
  const jestVersion = require('jest/package.json').version;

  console.log(`Test Environment:
    Node.js: ${nodeVersion}
    Jest: ${jestVersion}
    Memory: ${global.testUtils.getMemoryUsage().rss}MB RSS
  `);

  // Validate Node.js version
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  if (majorVersion < 14) {
    console.warn('Warning: Node.js version 14+ recommended for optimal performance');
  }
};

// Run environment validation
validateTestEnvironment();

module.exports = {
  testUtils: global.testUtils,
  testConfig: global.testConfig,
  mockFactories: global.mockFactories,
  testCleanup: global.testCleanup
};