/**
 * Mock Setup Configuration for Flow-Aware Error Handling Tests
 * Provides comprehensive mocking for external dependencies and services
 */

// External dependencies mocking
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  })),
  defaults: {
    timeout: 5000,
    headers: {}
  }
}));

jest.mock('redis', () => ({
  createClient: jest.fn(() => ({
    connect: jest.fn().mockResolvedValue(true),
    disconnect: jest.fn().mockResolvedValue(true),
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn(),
    exists: jest.fn(),
    expire: jest.fn(),
    ttl: jest.fn(),
    keys: jest.fn(),
    flushall: jest.fn(),
    on: jest.fn(),
    off: jest.fn()
  }))
}));

jest.mock('ws', () => ({
  Server: jest.fn(() => ({
    on: jest.fn(),
    close: jest.fn()
  })),
  WebSocket: jest.fn(() => ({
    send: jest.fn(),
    close: jest.fn(),
    on: jest.fn(),
    readyState: 1
  }))
}));

// Database mocking
jest.mock('pg', () => ({
  Client: jest.fn(() => ({
    connect: jest.fn().mockResolvedValue(true),
    end: jest.fn().mockResolvedValue(true),
    query: jest.fn().mockResolvedValue({ rows: [], rowCount: 0 })
  })),
  Pool: jest.fn(() => ({
    connect: jest.fn().mockResolvedValue({
      query: jest.fn().mockResolvedValue({ rows: [], rowCount: 0 }),
      release: jest.fn()
    }),
    end: jest.fn().mockResolvedValue(true),
    query: jest.fn().mockResolvedValue({ rows: [], rowCount: 0 })
  }))
}));

// Message queue mocking
jest.mock('amqplib', () => ({
  connect: jest.fn().mockResolvedValue({
    createChannel: jest.fn().mockResolvedValue({
      assertQueue: jest.fn().mockResolvedValue({}),
      sendToQueue: jest.fn(),
      consume: jest.fn(),
      ack: jest.fn(),
      nack: jest.fn(),
      close: jest.fn().mockResolvedValue(true)
    }),
    close: jest.fn().mockResolvedValue(true)
  })
}));

// Monitoring and metrics mocking
jest.mock('prom-client', () => ({
  Counter: jest.fn(() => ({
    inc: jest.fn(),
    get: jest.fn(() => ({ values: [] }))
  })),
  Gauge: jest.fn(() => ({
    set: jest.fn(),
    inc: jest.fn(),
    dec: jest.fn(),
    get: jest.fn(() => ({ values: [] }))
  })),
  Histogram: jest.fn(() => ({
    observe: jest.fn(),
    get: jest.fn(() => ({ values: [] }))
  })),
  Summary: jest.fn(() => ({
    observe: jest.fn(),
    get: jest.fn(() => ({ values: [] }))
  })),
  register: {
    metrics: jest.fn().mockResolvedValue(''),
    clear: jest.fn(),
    setDefaultLabels: jest.fn()
  }
}));

// Global mock implementations
global.mockImplementations = {
  // HTTP Client mock with realistic responses
  httpClient: {
    healthy: {
      status: 200,
      data: {
        status: 'healthy',
        uptime: 3600000,
        timestamp: Date.now()
      }
    },
    unhealthy: {
      status: 503,
      data: {
        status: 'unhealthy',
        error: 'Service unavailable',
        timestamp: Date.now()
      }
    },
    timeout: {
      code: 'ECONNABORTED',
      message: 'timeout of 5000ms exceeded'
    },
    networkError: {
      code: 'ENOTFOUND',
      message: 'getaddrinfo ENOTFOUND service.local'
    }
  },

  // Database mock responses
  database: {
    querySuccess: {
      rows: [
        { id: 1, name: 'test', created_at: new Date() }
      ],
      rowCount: 1
    },
    queryEmpty: {
      rows: [],
      rowCount: 0
    },
    insertSuccess: {
      rows: [{ id: 1 }],
      rowCount: 1
    },
    connectionError: new Error('Connection terminated')
  },

  // Message queue mock responses
  messageQueue: {
    sendSuccess: true,
    consumeMessage: {
      content: Buffer.from(JSON.stringify({ type: 'test', data: {} })),
      fields: { deliveryTag: 1 },
      properties: { messageId: 'msg_1' }
    }
  },

  // External service mock responses
  externalServices: {
    marketData: {
      success: {
        symbol: 'BTCUSD',
        price: 50000,
        volume: 1000000,
        timestamp: Date.now()
      },
      error: {
        error: 'Market closed',
        code: 'MARKET_CLOSED'
      }
    },

    paymentGateway: {
      success: {
        transactionId: 'tx_123456',
        status: 'completed',
        amount: 1000,
        currency: 'USD'
      },
      failure: {
        error: 'Payment failed',
        code: 'PAYMENT_FAILED',
        reason: 'Insufficient funds'
      }
    },

    riskEngine: {
      approved: {
        decision: 'approved',
        riskScore: 0.3,
        limits: { daily: 10000, single: 5000 }
      },
      rejected: {
        decision: 'rejected',
        riskScore: 0.9,
        reason: 'Risk threshold exceeded'
      }
    }
  }
};

// Mock service factory
global.createMockService = (serviceName, overrides = {}) => {
  const baseMock = {
    id: serviceName,
    name: serviceName.charAt(0).toUpperCase() + serviceName.slice(1),
    status: 'healthy',
    port: 3000 + Math.floor(Math.random() * 1000),
    healthEndpoint: `/health`,
    dependencies: [],
    responseTime: 100 + Math.random() * 50,
    errorRate: Math.random() * 0.01,
    availability: 0.99 + Math.random() * 0.01,
    lastCheck: Date.now(),
    ...overrides
  };

  return {
    ...baseMock,
    checkHealth: jest.fn().mockResolvedValue({
      status: baseMock.status,
      responseTime: baseMock.responseTime,
      timestamp: Date.now()
    }),
    restart: jest.fn().mockResolvedValue(true),
    stop: jest.fn().mockResolvedValue(true),
    start: jest.fn().mockResolvedValue(true),
    getMetrics: jest.fn().mockResolvedValue({
      requests: Math.floor(Math.random() * 1000),
      errors: Math.floor(Math.random() * 10),
      responseTime: baseMock.responseTime
    })
  };
};

// Mock test environment factory
global.createTestEnvironment = (config = {}) => {
  const environment = {
    services: new Map(),
    networks: new Map(),
    databases: new Map(),
    messageQueues: new Map(),
    config: {
      autoCleanup: true,
      networkLatency: 0,
      errorRate: 0,
      ...config
    }
  };

  return {
    // Service management
    addService: (name, serviceConfig) => {
      const service = global.createMockService(name, serviceConfig);
      environment.services.set(name, service);
      return service;
    },

    removeService: (name) => {
      return environment.services.delete(name);
    },

    getService: (name) => {
      return environment.services.get(name);
    },

    listServices: () => {
      return Array.from(environment.services.keys());
    },

    // Network simulation
    simulateNetworkLatency: (serviceId, latency) => {
      const service = environment.services.get(serviceId);
      if (service) {
        service.checkHealth = jest.fn().mockImplementation(async () => {
          await new Promise(resolve => setTimeout(resolve, latency));
          return {
            status: service.status,
            responseTime: service.responseTime + latency,
            timestamp: Date.now()
          };
        });
      }
    },

    simulateNetworkPartition: (serviceIds) => {
      serviceIds.forEach(serviceId => {
        const service = environment.services.get(serviceId);
        if (service) {
          service.checkHealth = jest.fn().mockRejectedValue(
            new Error('Network partition - service unreachable')
          );
        }
      });
    },

    // Failure injection
    injectServiceFailure: (serviceId, failureType, duration = 10000) => {
      const service = environment.services.get(serviceId);
      if (!service) return false;

      const originalHealthCheck = service.checkHealth;

      switch (failureType) {
        case 'crash':
          service.status = 'crashed';
          service.checkHealth = jest.fn().mockRejectedValue(
            new Error('Service crashed')
          );
          break;

        case 'hang':
          service.checkHealth = jest.fn().mockImplementation(
            () => new Promise(() => {}) // Never resolves
          );
          break;

        case 'slow_response':
          service.checkHealth = jest.fn().mockImplementation(async () => {
            await new Promise(resolve => setTimeout(resolve, 10000));
            return {
              status: 'degraded',
              responseTime: 10000,
              timestamp: Date.now()
            };
          });
          break;

        case 'intermittent':
          let failCount = 0;
          service.checkHealth = jest.fn().mockImplementation(async () => {
            failCount++;
            if (failCount % 3 === 0) {
              throw new Error('Intermittent failure');
            }
            return {
              status: 'healthy',
              responseTime: service.responseTime,
              timestamp: Date.now()
            };
          });
          break;
      }

      // Auto-recover after duration
      setTimeout(() => {
        service.status = 'healthy';
        service.checkHealth = originalHealthCheck;
      }, duration);

      return true;
    },

    // Resource management
    cleanup: () => {
      environment.services.clear();
      environment.networks.clear();
      environment.databases.clear();
      environment.messageQueues.clear();
    },

    // Health checks
    performHealthCheck: async () => {
      const results = new Map();

      for (const [name, service] of environment.services) {
        try {
          const health = await service.checkHealth();
          results.set(name, health);
        } catch (error) {
          results.set(name, {
            status: 'error',
            error: error.message,
            timestamp: Date.now()
          });
        }
      }

      return results;
    }
  };
};

// Mock chaos engineering tools
global.createChaosTools = () => {
  return {
    // Network chaos
    introduceLatency: (min, max) => {
      const latency = min + Math.random() * (max - min);
      return new Promise(resolve => setTimeout(resolve, latency));
    },

    dropPackets: (probability) => {
      return Math.random() < probability;
    },

    corruptData: (data, probability) => {
      if (Math.random() < probability) {
        const corrupted = JSON.stringify(data);
        const index = Math.floor(Math.random() * corrupted.length);
        return corrupted.substring(0, index) + 'X' + corrupted.substring(index + 1);
      }
      return data;
    },

    // Resource chaos
    exhaustMemory: (targetMB) => {
      const arrays = [];
      const targetBytes = targetMB * 1024 * 1024;
      let allocated = 0;

      while (allocated < targetBytes) {
        const chunk = new Array(1024 * 1024).fill('X'); // 1MB chunks
        arrays.push(chunk);
        allocated += chunk.length;
      }

      return () => arrays.length = 0; // Cleanup function
    },

    consumeCPU: (duration) => {
      const endTime = Date.now() + duration;
      while (Date.now() < endTime) {
        // Busy wait
        Math.random();
      }
    },

    // Service chaos
    killRandomService: (environment) => {
      const services = Array.from(environment.services.keys());
      if (services.length === 0) return null;

      const randomService = services[Math.floor(Math.random() * services.length)];
      environment.injectServiceFailure(randomService, 'crash');
      return randomService;
    },

    // Data chaos
    introduceDataInconsistency: (probability) => {
      return (data) => {
        if (Math.random() < probability) {
          // Introduce inconsistency
          const corrupted = { ...data };
          if (corrupted.id) corrupted.id = corrupted.id + '_corrupted';
          if (corrupted.timestamp) corrupted.timestamp = 0;
          return corrupted;
        }
        return data;
      };
    }
  };
};

// Performance monitoring mocks
global.mockPerformanceMonitor = {
  startTimer: jest.fn(() => {
    const start = Date.now();
    return {
      end: jest.fn(() => Date.now() - start)
    };
  }),

  recordMetric: jest.fn(),
  incrementCounter: jest.fn(),
  setGauge: jest.fn(),
  observeHistogram: jest.fn(),

  getMetrics: jest.fn(() => ({
    counters: {},
    gauges: {},
    histograms: {},
    timers: {}
  })),

  reset: jest.fn()
};

// Alerting system mocks
global.mockAlertingSystem = {
  sendAlert: jest.fn().mockResolvedValue({ success: true, alertId: 'alert_123' }),
  escalateAlert: jest.fn().mockResolvedValue({ success: true }),
  resolveAlert: jest.fn().mockResolvedValue({ success: true }),
  getActiveAlerts: jest.fn().mockResolvedValue([]),
  configureChannel: jest.fn().mockResolvedValue({ success: true })
};

// Load testing utilities
global.mockLoadTester = {
  generateLoad: async (config) => {
    const {
      requestsPerSecond = 10,
      duration = 10000,
      target = () => Promise.resolve(),
      rampUp = false
    } = config;

    const results = [];
    const interval = 1000 / requestsPerSecond;
    const endTime = Date.now() + duration;

    while (Date.now() < endTime) {
      const start = Date.now();

      try {
        await target();
        results.push({
          timestamp: start,
          responseTime: Date.now() - start,
          success: true
        });
      } catch (error) {
        results.push({
          timestamp: start,
          responseTime: Date.now() - start,
          success: false,
          error: error.message
        });
      }

      // Wait for next request
      const elapsed = Date.now() - start;
      const waitTime = Math.max(0, interval - elapsed);
      if (waitTime > 0) {
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    return {
      totalRequests: results.length,
      successfulRequests: results.filter(r => r.success).length,
      failedRequests: results.filter(r => !r.success).length,
      averageResponseTime: results.reduce((sum, r) => sum + r.responseTime, 0) / results.length,
      minResponseTime: Math.min(...results.map(r => r.responseTime)),
      maxResponseTime: Math.max(...results.map(r => r.responseTime)),
      results
    };
  }
};

// Custom mock assertions
global.expectMockToHaveBeenCalledWithPattern = (mockFn, pattern) => {
  const calls = mockFn.mock.calls;
  const matchingCall = calls.find(call => {
    return call.some(arg => {
      if (typeof pattern === 'string') {
        return JSON.stringify(arg).includes(pattern);
      }
      if (typeof pattern === 'object') {
        return Object.keys(pattern).every(key => arg[key] === pattern[key]);
      }
      return false;
    });
  });

  expect(matchingCall).toBeDefined();
};

// Environment cleanup
const originalConsoleWarn = console.warn;
console.warn = (...args) => {
  const message = args.join(' ');

  // Suppress known test-related warnings
  const suppressedWarnings = [
    'deprecated',
    'experimental',
    'warning'
  ];

  if (!suppressedWarnings.some(warning => message.toLowerCase().includes(warning))) {
    originalConsoleWarn.apply(console, args);
  }
};

module.exports = {
  mockImplementations: global.mockImplementations,
  createMockService: global.createMockService,
  createTestEnvironment: global.createTestEnvironment,
  createChaosTools: global.createChaosTools,
  mockPerformanceMonitor: global.mockPerformanceMonitor,
  mockAlertingSystem: global.mockAlertingSystem,
  mockLoadTester: global.mockLoadTester
};