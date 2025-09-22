/**
 * Test Helper Utilities for Flow-Aware Error Handling Tests
 * Provides common utilities and helper functions for all test categories
 */

const { v4: uuidv4 } = require('uuid');

// ID Generators
const generateFlowId = () => `flow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const generateServiceId = () => `service_${Math.random().toString(36).substr(2, 8)}`;
const generateChainId = () => `chain_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
const generateErrorId = () => `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Mock Object Creators
const createMockError = (overrides = {}) => ({
  id: generateErrorId(),
  serviceId: 'test-service',
  type: 'test_error',
  severity: 'medium',
  message: 'Test error message',
  timestamp: Date.now(),
  stack: 'Test stack trace',
  metadata: {},
  ...overrides
});

const createMockService = (overrides = {}) => ({
  id: generateServiceId(),
  name: 'Test Service',
  healthEndpoint: 'http://localhost:3000/health',
  dependencies: [],
  criticality: 'medium',
  status: 'healthy',
  responseTime: 100 + Math.random() * 50,
  errorRate: Math.random() * 0.01,
  availability: 0.99 + Math.random() * 0.01,
  ...overrides
});

const createMockFlow = (overrides = {}) => ({
  id: generateFlowId(),
  serviceId: 'test-service',
  status: 'pending',
  timestamp: Date.now(),
  metadata: {},
  steps: [],
  errors: [],
  duration: null,
  ...overrides
});

// Timing Utilities
const waitForCondition = async (condition, timeout = 10000, interval = 100) => {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Condition not met within ${timeout}ms`);
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const withTimeout = async (promise, timeout, errorMessage = 'Operation timed out') => {
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error(errorMessage)), timeout);
  });

  return Promise.race([promise, timeoutPromise]);
};

// Performance Measurement
const measurePerformance = async (fn, iterations = 1) => {
  const times = [];
  const memoryBefore = process.memoryUsage();

  for (let i = 0; i < iterations; i++) {
    const start = process.hrtime.bigint();
    await fn();
    const end = process.hrtime.bigint();
    times.push(Number(end - start) / 1000000); // Convert to milliseconds
  }

  const memoryAfter = process.memoryUsage();

  times.sort((a, b) => a - b);

  return {
    min: times[0],
    max: times[times.length - 1],
    avg: times.reduce((a, b) => a + b, 0) / times.length,
    median: times[Math.floor(times.length / 2)],
    p95: times[Math.floor(times.length * 0.95)],
    p99: times[Math.floor(times.length * 0.99)],
    total: times.reduce((a, b) => a + b, 0),
    times,
    iterations,
    memoryDelta: {
      heapUsed: memoryAfter.heapUsed - memoryBefore.heapUsed,
      heapTotal: memoryAfter.heapTotal - memoryBefore.heapTotal,
      external: memoryAfter.external - memoryBefore.external
    }
  };
};

const benchmarkFunction = async (fn, options = {}) => {
  const {
    iterations = 100,
    warmupIterations = 10,
    timeout = 30000,
    name = 'Benchmark'
  } = options;

  console.log(`Starting benchmark: ${name}`);

  // Warmup
  for (let i = 0; i < warmupIterations; i++) {
    await fn();
  }

  // Force garbage collection if available
  if (global.gc) global.gc();

  // Actual benchmark
  const result = await measurePerformance(fn, iterations);

  console.log(`Benchmark ${name} completed:
    Iterations: ${iterations}
    Average: ${result.avg.toFixed(2)}ms
    P95: ${result.p95.toFixed(2)}ms
    P99: ${result.p99.toFixed(2)}ms
    Memory Delta: ${(result.memoryDelta.heapUsed / 1024 / 1024).toFixed(2)}MB
  `);

  return result;
};

// Memory Utilities
const getMemoryUsage = () => {
  const usage = process.memoryUsage();
  return {
    heapUsed: Math.round(usage.heapUsed / 1024 / 1024), // MB
    heapTotal: Math.round(usage.heapTotal / 1024 / 1024), // MB
    external: Math.round(usage.external / 1024 / 1024), // MB
    rss: Math.round(usage.rss / 1024 / 1024) // MB
  };
};

const forceGarbageCollection = () => {
  if (global.gc) {
    global.gc();
    return true;
  }
  return false;
};

const trackMemoryLeaks = (testFn, threshold = 10) => {
  return async () => {
    const initialMemory = getMemoryUsage();

    await testFn();

    // Force GC and wait
    forceGarbageCollection();
    await sleep(100);
    forceGarbageCollection();

    const finalMemory = getMemoryUsage();
    const memoryGrowth = finalMemory.heapUsed - initialMemory.heapUsed;

    if (memoryGrowth > threshold) {
      console.warn(`Potential memory leak detected: ${memoryGrowth}MB growth`);
    }

    return {
      initialMemory,
      finalMemory,
      memoryGrowth,
      potentialLeak: memoryGrowth > threshold
    };
  };
};

// Data Generation
const generateRandomData = (size, options = {}) => {
  const {
    type = 'object',
    complexity = 'simple',
    includeTimestamp = true
  } = options;

  const data = [];

  for (let i = 0; i < size; i++) {
    let item;

    switch (type) {
      case 'string':
        item = Math.random().toString(36).substr(2, 15);
        break;
      case 'number':
        item = Math.random() * 1000;
        break;
      case 'object':
      default:
        item = {
          id: i,
          value: Math.random() * 1000,
          category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
          active: Math.random() > 0.5
        };

        if (includeTimestamp) {
          item.timestamp = Date.now() - (Math.random() * 86400000); // Random within 24h
        }

        if (complexity === 'complex') {
          item.nested = {
            level1: {
              level2: {
                data: Array.from({ length: 10 }, () => Math.random())
              }
            }
          };
          item.array = Array.from({ length: 5 }, (_, j) => ({ index: j, value: Math.random() }));
        }
        break;
    }

    data.push(item);
  }

  return data;
};

const generateLoadPattern = (options = {}) => {
  const {
    duration = 60000, // 1 minute
    peakRPS = 100,
    pattern = 'constant', // constant, ramp-up, spike, wave
    baselineRPS = 10
  } = options;

  const points = [];
  const interval = 1000; // 1 second intervals
  const totalPoints = duration / interval;

  for (let i = 0; i < totalPoints; i++) {
    const time = i * interval;
    const progress = i / totalPoints;
    let rps;

    switch (pattern) {
      case 'ramp-up':
        rps = baselineRPS + (peakRPS - baselineRPS) * progress;
        break;
      case 'ramp-down':
        rps = peakRPS - (peakRPS - baselineRPS) * progress;
        break;
      case 'spike':
        if (progress >= 0.4 && progress <= 0.6) {
          rps = peakRPS;
        } else {
          rps = baselineRPS;
        }
        break;
      case 'wave':
        rps = baselineRPS + (peakRPS - baselineRPS) *
              (0.5 + 0.5 * Math.sin(2 * Math.PI * progress));
        break;
      case 'burst':
        rps = (Math.floor(progress * 10) % 3 === 0) ? peakRPS : baselineRPS;
        break;
      default: // constant
        rps = peakRPS;
    }

    points.push({ time, rps: Math.round(rps) });
  }

  return points;
};

// Test Environment Helpers
const createTestServer = (port = 0, routes = {}) => {
  const express = require('express');
  const app = express();

  app.use(express.json());

  // Default health endpoint
  app.get('/health', (req, res) => {
    res.json({
      status: 'healthy',
      timestamp: Date.now(),
      uptime: process.uptime()
    });
  });

  // Add custom routes
  Object.entries(routes).forEach(([path, handler]) => {
    if (typeof handler === 'function') {
      app.get(path, handler);
    } else {
      app.get(path, (req, res) => res.json(handler));
    }
  });

  return new Promise((resolve) => {
    const server = app.listen(port, () => {
      const actualPort = server.address().port;
      resolve({
        app,
        server,
        port: actualPort,
        url: `http://localhost:${actualPort}`,
        stop: () => new Promise(resolve => server.close(resolve))
      });
    });
  });
};

const createMockDatabase = () => {
  const data = new Map();

  return {
    connect: jest.fn().mockResolvedValue(true),
    disconnect: jest.fn().mockResolvedValue(true),

    query: jest.fn().mockImplementation(async (sql, params) => {
      // Simple mock implementation
      if (sql.includes('SELECT')) {
        return { rows: Array.from(data.values()), rowCount: data.size };
      }
      return { rows: [], rowCount: 0 };
    }),

    insert: jest.fn().mockImplementation(async (table, record) => {
      const id = record.id || uuidv4();
      data.set(id, { ...record, id });
      return { rows: [{ id }], rowCount: 1 };
    }),

    update: jest.fn().mockImplementation(async (table, id, updates) => {
      if (data.has(id)) {
        data.set(id, { ...data.get(id), ...updates });
        return { rows: [data.get(id)], rowCount: 1 };
      }
      return { rows: [], rowCount: 0 };
    }),

    delete: jest.fn().mockImplementation(async (table, id) => {
      const deleted = data.delete(id);
      return { rows: [], rowCount: deleted ? 1 : 0 };
    }),

    clear: () => data.clear(),
    size: () => data.size,

    // For testing
    _getData: () => data,
    _setData: (newData) => {
      data.clear();
      Object.entries(newData).forEach(([k, v]) => data.set(k, v));
    }
  };
};

// Error Simulation
const simulateError = (type, probability = 1.0, delay = 0) => {
  return async () => {
    if (Math.random() > probability) {
      return; // No error
    }

    if (delay > 0) {
      await sleep(delay);
    }

    switch (type) {
      case 'network':
        throw new Error('Network error - Connection refused');
      case 'timeout':
        throw new Error('Request timeout');
      case 'database':
        throw new Error('Database connection failed');
      case 'validation':
        throw new Error('Validation failed');
      case 'permission':
        throw new Error('Access denied');
      case 'rate_limit':
        throw new Error('Rate limit exceeded');
      default:
        throw new Error(`Simulated error: ${type}`);
    }
  };
};

const simulateServiceError = async (service, errorConfig) => {
  const { type, duration = 5000, errorRate = 1.0 } = errorConfig;

  const originalFunction = service.checkHealth || service.process || (() => Promise.resolve());

  switch (type) {
    case 'connection_timeout':
      service.checkHealth = () => {
        throw new Error('Connection timeout');
      };
      break;

    case 'sustained_failure':
      service.checkHealth = () => {
        if (Math.random() < errorRate) {
          throw new Error('Sustained failure');
        }
        return Promise.resolve({ status: 'healthy' });
      };
      break;

    case 'gradual_degradation':
      let degradationLevel = 0;
      const degradationInterval = setInterval(() => {
        degradationLevel += errorConfig.degradationRate || 0.1;
      }, 1000);

      service.checkHealth = () => {
        if (Math.random() < degradationLevel) {
          throw new Error('Gradual degradation');
        }
        return Promise.resolve({ status: 'healthy' });
      };

      setTimeout(() => {
        clearInterval(degradationInterval);
        service.checkHealth = originalFunction;
      }, duration);
      return;

    case 'processing_delay':
      service.checkHealth = async () => {
        await sleep(errorConfig.delay || 1000);
        return { status: 'healthy' };
      };
      break;
  }

  // Auto-restore after duration
  setTimeout(() => {
    service.checkHealth = originalFunction;
  }, duration);
};

// Assertion Helpers
const waitForPropagation = (ms = 1000) => sleep(ms);

const expectEventually = async (assertion, timeout = 5000, interval = 100) => {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      await assertion();
      return; // Assertion passed
    } catch (error) {
      await sleep(interval);
    }
  }

  // Final attempt - let it throw if it fails
  await assertion();
};

const expectWithinRange = (actual, expected, tolerance) => {
  const diff = Math.abs(actual - expected);
  const toleranceValue = typeof tolerance === 'number' ? tolerance : expected * tolerance;

  if (diff > toleranceValue) {
    throw new Error(
      `Expected ${actual} to be within ${toleranceValue} of ${expected}, but difference was ${diff}`
    );
  }
};

// Export all utilities
module.exports = {
  // ID Generators
  generateFlowId,
  generateServiceId,
  generateChainId,
  generateErrorId,

  // Mock Creators
  createMockError,
  createMockService,
  createMockFlow,

  // Timing
  waitForCondition,
  sleep,
  withTimeout,

  // Performance
  measurePerformance,
  benchmarkFunction,

  // Memory
  getMemoryUsage,
  forceGarbageCollection,
  trackMemoryLeaks,

  // Data Generation
  generateRandomData,
  generateLoadPattern,

  // Test Environment
  createTestServer,
  createMockDatabase,

  // Error Simulation
  simulateError,
  simulateServiceError,

  // Assertions
  waitForPropagation,
  expectEventually,
  expectWithinRange
};