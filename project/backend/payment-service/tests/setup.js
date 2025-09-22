const mongoose = require('mongoose');

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error';

// Mock external services
jest.mock('../src/config/redis', () => ({
  connect: jest.fn().mockResolvedValue(),
  disconnect: jest.fn().mockResolvedValue(),
  getClient: jest.fn().mockReturnValue({
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn(),
    setex: jest.fn()
  }),
  getConnectionStatus: jest.fn().mockReturnValue({ isConnected: true }),
  setCache: jest.fn().mockResolvedValue(),
  getCache: jest.fn().mockResolvedValue(null),
  deleteCache: jest.fn().mockResolvedValue()
}));

// Mock Midtrans SDK
jest.mock('midtrans-client', () => ({
  CoreApi: jest.fn().mockImplementation(() => ({
    charge: jest.fn(),
    transaction: {
      status: jest.fn(),
      approve: jest.fn(),
      cancel: jest.fn(),
      refund: jest.fn()
    }
  })),
  Snap: jest.fn().mockImplementation(() => ({
    createTransaction: jest.fn()
  })),
  Iris: jest.fn().mockImplementation(() => ({
    ping: jest.fn()
  }))
}));

// Mock logger to reduce test noise
jest.mock('../src/config/logger', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
}));

// Global test setup
beforeAll(async () => {
  // Disable mongoose warnings
  mongoose.set('strictQuery', false);
});

// Clean up after all tests
afterAll(async () => {
  // Close all mongoose connections
  await mongoose.disconnect();
});

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
});

// Global error handler for tests
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Set longer timeout for integration tests
jest.setTimeout(30000);