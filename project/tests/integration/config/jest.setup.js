/**
 * Jest Setup for Integration Tests
 * Global test configuration and utilities
 */

// Set test environment
process.env.NODE_ENV = 'test';

// Increase timeout for integration tests
jest.setTimeout(30000);

// Global test setup
beforeAll(async () => {
  console.log('🔧 Setting up integration test environment...');

  // Ensure test environment variables
  if (!process.env.NODE_ENV) {
    process.env.NODE_ENV = 'test';
  }

  // Set default database connection parameters for tests
  if (!process.env.DB_HOST) {
    process.env.DB_HOST = 'localhost';
  }

  if (!process.env.DB_PORT) {
    process.env.DB_PORT = '5432';
  }

  if (!process.env.DB_USER) {
    process.env.DB_USER = 'postgres';
  }

  if (!process.env.DB_PASSWORD) {
    process.env.DB_PASSWORD = 'postgres';
  }
});

// Global test cleanup
afterAll(async () => {
  console.log('🧹 Cleaning up test environment...');

  // Close any open handles
  if (global.gc) {
    global.gc();
  }
});

// Custom matchers
expect.extend({
  toBeHealthy(received) {
    const pass = received && received.isHealthy === true && received.status === 200;
    if (pass) {
      return {
        message: () => `expected service not to be healthy`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected service to be healthy, but got: ${JSON.stringify(received)}`,
        pass: false,
      };
    }
  },

  toHaveValidPort(received) {
    const port = typeof received === 'object' ? received.port : received;
    const pass = typeof port === 'number' && port > 0 && port < 65536;
    if (pass) {
      return {
        message: () => `expected ${port} not to be a valid port`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${port} to be a valid port number (1-65535)`,
        pass: false,
      };
    }
  },

  toBeAccessible(received) {
    const pass = received && (received.accessible === true || received.status < 500);
    if (pass) {
      return {
        message: () => `expected service not to be accessible`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected service to be accessible, but got: ${JSON.stringify(received)}`,
        pass: false,
      };
    }
  }
});

// Error handling for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

console.log('✅ Jest integration test setup complete');