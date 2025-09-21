/**
 * Jest Configuration for AI Trading Platform
 * Comprehensive testing setup for microservices workspace
 */

module.exports = {
  // Project root
  rootDir: '.',

  // Test environment
  testEnvironment: 'node',

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Transform configuration
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },

  // Test match patterns
  testMatch: [
    '**/tests/**/*.(test|spec).(ts|js)',
    '**/*.(test|spec).(ts|js)',
    '!**/node_modules/**',
    '!**/dist/**'
  ],

  // Coverage configuration
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  collectCoverageFrom: [
    'shared/src/**/*.{ts,js}',
    'api-gateway/src/**/*.{ts,js}',
    'central-hub/src/**/*.{ts,js}',
    'database-service/src/**/*.{ts,js}',
    'data-bridge/src/**/*.{ts,js}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/dist/**',
    '!**/coverage/**',
    '!**/*.config.{ts,js}',
    '!**/tests/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './shared/src/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },

  // Module name mapping
  moduleNameMapping: {
    '^@aitrading/shared$': '<rootDir>/shared/src',
    '^@aitrading/shared/(.*)$': '<rootDir>/shared/src/$1',
    '^@shared/(.*)$': '<rootDir>/shared/src/$1'
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Test timeout
  testTimeout: 30000,

  // Max workers
  maxWorkers: '50%',

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,

  // Error handling
  errorOnDeprecated: true,

  // Global setup/teardown
  globalSetup: '<rootDir>/jest.global-setup.js',
  globalTeardown: '<rootDir>/jest.global-teardown.js',

  // Projects configuration for workspace
  projects: [
    {
      displayName: 'shared',
      testMatch: ['<rootDir>/shared/**/*.(test|spec).(ts|js)'],
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
    },
    {
      displayName: 'api-gateway',
      testMatch: ['<rootDir>/api-gateway/**/*.(test|spec).(ts|js)'],
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
    },
    {
      displayName: 'central-hub',
      testMatch: ['<rootDir>/central-hub/**/*.(test|spec).(ts|js)'],
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
    },
    {
      displayName: 'database-service',
      testMatch: ['<rootDir>/database-service/**/*.(test|spec).(ts|js)'],
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
    },
    {
      displayName: 'data-bridge',
      testMatch: ['<rootDir>/data-bridge/**/*.(test|spec).(ts|js)'],
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
    }
  ]
};