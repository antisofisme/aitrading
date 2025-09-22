// Jest setup file for trading engine tests

// Set test environment
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error'; // Reduce logging noise in tests
process.env.REDIS_HOST = 'localhost';
process.env.REDIS_PORT = '6379';
process.env.DATA_BRIDGE_URL = 'http://localhost:3002';
process.env.TARGET_LATENCY = '10';
process.env.MAX_LATENCY = '50';

// Increase test timeout for integration tests
jest.setTimeout(30000);

// Mock Redis if not available
jest.mock('redis', () => ({
  createClient: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    set: jest.fn(),
    get: jest.fn(),
    del: jest.fn(),
    on: jest.fn()
  }))
}));

// Mock WebSocket for tests
global.WebSocket = jest.fn(() => ({
  send: jest.fn(),
  close: jest.fn(),
  on: jest.fn(),
  readyState: 1, // OPEN
  OPEN: 1,
  CLOSED: 3
}));

// Global test utilities
global.createMockOrder = (overrides = {}) => ({
  symbol: 'EURUSD',
  side: 'buy',
  quantity: 10000,
  type: 'market',
  ...overrides
});

global.createMockMarketData = (symbol = 'EURUSD', overrides = {}) => ({
  symbol,
  bid: 1.0500,
  ask: 1.0502,
  spread: 0.0002,
  timestamp: Date.now(),
  volume: 1000,
  ...overrides
});

global.createMockExecution = (orderId, overrides = {}) => ({
  id: `exec_${Date.now()}`,
  orderId,
  symbol: 'EURUSD',
  side: 'buy',
  quantity: 10000,
  price: 1.0502,
  commission: 2.1,
  timestamp: Date.now(),
  ...overrides
});

// Mock performance.now for consistent timing tests
if (!global.performance) {
  global.performance = {
    now: jest.fn(() => Date.now())
  };
}

// Clean up after each test
afterEach(() => {
  jest.clearAllTimers();
  jest.clearAllMocks();
});

// Handle unhandled promise rejections in tests
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Handle uncaught exceptions in tests
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});