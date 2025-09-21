/**
 * Jest Setup Configuration
 * Common test setup for all microservices
 */

// Set environment variables for testing
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error';

// Increase timeout for integration tests
jest.setTimeout(30000);

// Mock external services in test environment
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
    patch: jest.fn()
  }))
}));

// Mock Redis
jest.mock('ioredis', () => {
  const mockRedis = {
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn(),
    exists: jest.fn(),
    expire: jest.fn(),
    ttl: jest.fn(),
    keys: jest.fn(),
    flushall: jest.fn(),
    quit: jest.fn(),
    disconnect: jest.fn(),
    ping: jest.fn(() => Promise.resolve('PONG')),
    on: jest.fn(),
    off: jest.fn()
  };
  return jest.fn(() => mockRedis);
});

// Mock Consul
jest.mock('consul', () => {
  return jest.fn(() => ({
    agent: {
      service: {
        register: jest.fn(),
        deregister: jest.fn(),
        list: jest.fn()
      },
      check: {
        pass: jest.fn(),
        fail: jest.fn()
      }
    },
    health: {
      service: jest.fn()
    },
    kv: {
      get: jest.fn(),
      set: jest.fn(),
      del: jest.fn()
    },
    status: {
      leader: jest.fn()
    },
    watch: jest.fn(() => ({
      on: jest.fn(),
      end: jest.fn()
    }))
  }));
});

// Mock Winston logger
jest.mock('winston', () => ({
  createLogger: jest.fn(() => ({
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
    log: jest.fn()
  })),
  format: {
    json: jest.fn(),
    combine: jest.fn(),
    timestamp: jest.fn(),
    errors: jest.fn(),
    colorize: jest.fn(),
    printf: jest.fn()
  },
  transports: {
    Console: jest.fn(),
    File: jest.fn()
  }
}));

// Mock winston-daily-rotate-file
jest.mock('winston-daily-rotate-file', () => jest.fn());

// Mock database connections
const mockPool = {
  query: jest.fn(),
  connect: jest.fn(),
  end: jest.fn(),
  release: jest.fn()
};

jest.mock('pg', () => ({
  Pool: jest.fn(() => mockPool),
  Client: jest.fn(() => ({
    connect: jest.fn(),
    query: jest.fn(),
    end: jest.fn(),
    release: jest.fn()
  }))
}));

// Mock MongoDB
jest.mock('mongodb', () => ({
  MongoClient: {
    connect: jest.fn(() => Promise.resolve({
      db: jest.fn(() => ({
        collection: jest.fn(() => ({
          find: jest.fn(),
          findOne: jest.fn(),
          insertOne: jest.fn(),
          insertMany: jest.fn(),
          updateOne: jest.fn(),
          updateMany: jest.fn(),
          deleteOne: jest.fn(),
          deleteMany: jest.fn(),
          countDocuments: jest.fn(),
          createIndex: jest.fn()
        }))
      })),
      close: jest.fn()
    }))
  }
}));

// Global test utilities
global.testUtils = {
  createMockLogger: () => ({
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
    trace: jest.fn(),
    audit: jest.fn(),
    performance: jest.fn(),
    security: jest.fn(),
    child: jest.fn(() => global.testUtils.createMockLogger()),
    setContext: jest.fn()
  }),

  createMockServiceRegistry: () => ({
    register: jest.fn(),
    deregister: jest.fn(),
    discoverServices: jest.fn(),
    getService: jest.fn(),
    getHealthyInstances: jest.fn(),
    getBalancedInstance: jest.fn(),
    setConfig: jest.fn(),
    getConfig: jest.fn(),
    watchServices: jest.fn(),
    isServiceRegistered: jest.fn(() => true)
  }),

  createMockHealthChecker: () => ({
    checkHealth: jest.fn(() => Promise.resolve({
      status: 'healthy',
      timestamp: new Date(),
      version: '1.0.0',
      uptime: 1000,
      environment: 'test',
      dependencies: []
    })),
    addDependency: jest.fn(),
    removeDependency: jest.fn(),
    getLastHealthCheck: jest.fn(),
    getUptime: jest.fn(() => 1000),
    getStartTime: jest.fn(() => new Date()),
    stopMetricsCollection: jest.fn()
  }),

  createMockRequest: (options = {}) => ({
    method: 'GET',
    url: '/',
    headers: {},
    query: {},
    params: {},
    body: {},
    user: null,
    ip: '127.0.0.1',
    get: jest.fn(),
    ...options
  }),

  createMockResponse: () => {
    const res = {
      status: jest.fn(() => res),
      json: jest.fn(() => res),
      send: jest.fn(() => res),
      end: jest.fn(() => res),
      get: jest.fn(),
      set: jest.fn(),
      statusCode: 200,
      locals: {}
    };
    return res;
  },

  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  generateId: () => `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,

  createTestDatabase: async () => {
    // Mock implementation for test database
    return {
      connect: jest.fn(),
      disconnect: jest.fn(),
      clean: jest.fn(),
      seed: jest.fn()
    };
  }
};

// Console warnings for unmocked dependencies
const originalConsoleWarn = console.warn;
console.warn = (...args) => {
  // Suppress specific warnings in tests
  const message = args[0];
  if (typeof message === 'string') {
    if (message.includes('DeprecationWarning') ||
        message.includes('ExperimentalWarning')) {
      return;
    }
  }
  originalConsoleWarn.apply(console, args);
};

// Error handling for tests
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  // Don't exit in test environment
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});

// Global teardown
afterAll(async () => {
  // Close any open handles
  await new Promise(resolve => setTimeout(resolve, 100));
});