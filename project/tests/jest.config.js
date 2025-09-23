/**
 * Enhanced Jest Configuration for AI Pipeline End-to-End Testing
 * Supports both TypeScript and JavaScript tests with comprehensive coverage
 */

module.exports = {
  displayName: 'AI Pipeline E2E Tests',
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>'],

  // Test file patterns - support both TS and JS
  testMatch: [
    '**/__tests__/**/*.+(ts|tsx|js)',
    '**/*.(test|spec).+(ts|tsx|js)'
  ],

  // Transform configuration
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.js$': 'babel-jest'
  },

  // Extended test timeout for AI pipeline tests
  testTimeout: 60000, // 60 seconds for comprehensive E2E tests

  // Coverage configuration with AI pipeline focus
  collectCoverageFrom: [
    '../backend/**/*.{js,ts}',
    '../src/**/*.{js,ts}',
    '../client/**/*.{js,ts}',
    '../web/**/*.{js,ts}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/coverage/**',
    '!**/tests/**'
  ],

  // Enhanced coverage reporting
  coverageReporters: ['text', 'lcov', 'html', 'json-summary', 'json'],
  coverageDirectory: './coverage',

  // Higher coverage thresholds for AI pipeline components
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 85,
      lines: 85,
      statements: 85
    },
    // Specific thresholds for critical AI components
    '../backend/ai-orchestration/**/*.js': {
      branches: 90,
      functions: 95,
      lines: 95,
      statements: 95
    },
    '../backend/data-bridge/**/*.js': {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },

  // Setup files for AI pipeline testing
  setupFilesAfterEnv: [
    '<rootDir>/setup/jest.setup.js',
    '<rootDir>/setup/test-setup.js'
  ],

  // Global setup and teardown for comprehensive testing
  globalSetup: '<rootDir>/setup/global-setup.js',
  globalTeardown: '<rootDir>/setup/global-teardown.js',

  // Performance settings for AI pipeline tests
  maxWorkers: '50%', // Use 50% of available cores
  workerIdleMemoryLimit: '512MB',

  // Advanced test runner for better performance
  testRunner: 'jest-circus/runner',

  // Enhanced module path mapping
  moduleNameMapping: {
    '^@backend/(.*)$': '<rootDir>/../backend/$1',
    '^@client/(.*)$': '<rootDir>/../client/$1',
    '^@web/(.*)$': '<rootDir>/../web/$1',
    '^@tests/(.*)$': '<rootDir>/$1',
    '^@utils/(.*)$': '<rootDir>/utils/$1',
    '^@mocks/(.*)$': '<rootDir>/mocks/$1'
  },

  // Enhanced reporters for AI pipeline testing
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: '<rootDir>/coverage/html-report',
      filename: 'ai-pipeline-test-report.html',
      expand: true,
      hideIcon: false,
      pageTitle: 'AI Pipeline End-to-End Test Report'
    }],
    ['jest-junit', {
      outputDirectory: '<rootDir>/coverage',
      outputName: 'junit.xml',
      suiteName: 'AI Pipeline E2E Tests'
    }]
  ],

  // TypeScript and Babel configuration
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json',
      isolatedModules: true
    }
  },

  // Mock configuration
  clearMocks: true,
  restoreMocks: true,
  resetMocks: false,

  // Error handling
  errorOnDeprecated: true,
  bail: false, // Continue running tests even if some fail

  // Verbose output for AI pipeline debugging
  verbose: true,

  // Cache configuration
  cacheDirectory: '<rootDir>/.jest-cache',

  // Test environment options
  testEnvironmentOptions: {
    NODE_ENV: 'test'
  }
};