// Jest setup file for ErrorDNA tests

const fs = require('fs-extra');
const path = require('path');

// Global test setup
beforeAll(async () => {
  // Ensure test directory exists
  const testDir = '/tmp/error-dna-test';
  await fs.ensureDir(testDir);

  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error'; // Reduce logging during tests
});

// Cleanup after all tests
afterAll(async () => {
  // Clean up test files
  const testDir = '/tmp/error-dna-test';
  if (await fs.pathExists(testDir)) {
    await fs.remove(testDir);
  }
});

// Global error handler for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  // Don't exit process during tests
});

// Suppress console.log during tests unless explicitly needed
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

beforeEach(() => {
  // Mock console methods to reduce test output noise
  console.log = jest.fn();
  console.warn = jest.fn();
  // Keep console.error for debugging test failures
  // console.error = jest.fn();
});

afterEach(() => {
  // Restore console methods
  console.log = originalConsoleLog;
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;

  // Clear all mocks
  jest.clearAllMocks();
});

// Custom matchers for ErrorDNA specific assertions
expect.extend({
  toBeValidErrorCategory(received) {
    const validCategories = ['SYSTEM', 'API', 'TRADING', 'AI_ML', 'USER', 'UNKNOWN'];
    const pass = validCategories.includes(received);

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid error category`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid error category (one of: ${validCategories.join(', ')})`,
        pass: false,
      };
    }
  },

  toBeValidSeverity(received) {
    const validSeverities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    const pass = validSeverities.includes(received);

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid severity level`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid severity level (one of: ${validSeverities.join(', ')})`,
        pass: false,
      };
    }
  },

  toHaveValidErrorStructure(received) {
    const requiredFields = ['category', 'severity', 'confidence', 'tags', 'metadata'];
    const hasAllFields = requiredFields.every(field => received.hasOwnProperty(field));

    if (hasAllFields) {
      return {
        message: () => `expected error object not to have valid structure`,
        pass: true,
      };
    } else {
      const missingFields = requiredFields.filter(field => !received.hasOwnProperty(field));
      return {
        message: () => `expected error object to have all required fields. Missing: ${missingFields.join(', ')}`,
        pass: false,
      };
    }
  }
});

// Global test utilities
global.createMockError = (overrides = {}) => {
  return {
    message: 'Test error message',
    stack: 'Error: Test error\n    at Test.function (test.js:1:1)',
    code: 'TEST_ERROR',
    type: 'TestError',
    timestamp: new Date().toISOString(),
    ...overrides
  };
};

global.createMockCategorizedError = (overrides = {}) => {
  return {
    id: `test_error_${Date.now()}`,
    originalError: createMockError(),
    categorization: {
      category: 'SYSTEM',
      subcategory: 'GENERAL',
      severity: 'MEDIUM',
      confidence: 0.8,
      tags: ['test'],
      metadata: {
        timestamp: new Date().toISOString(),
        analyzed: true,
        errorType: 'TestError',
        source: 'test'
      }
    },
    patterns: [],
    context: {},
    metadata: {
      timestamp: new Date().toISOString()
    },
    ...overrides
  };
};

global.waitFor = (ms) => new Promise(resolve => setTimeout(resolve, ms));

global.expectEventually = async (expectation, timeout = 5000, interval = 100) => {
  const start = Date.now();
  let lastError;

  while (Date.now() - start < timeout) {
    try {
      await expectation();
      return;
    } catch (error) {
      lastError = error;
      await waitFor(interval);
    }
  }

  throw lastError || new Error('Expectation timeout');
};