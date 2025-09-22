/**
 * Jest Configuration for Flow-Aware Error Handling Test Suite
 * Comprehensive testing setup with coverage, performance, and CI/CD integration
 */

module.exports = {
  displayName: 'Flow-Aware Error Handling Tests',
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>'],

  // Test file patterns
  testMatch: [
    '**/unit/**/*.test.js',
    '**/integration/**/*.test.js',
    '**/e2e/**/*.test.js',
    '**/performance/**/*.test.js',
    '**/chaos/**/*.test.js'
  ],

  // Transform configuration
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Extended timeout for flow-aware debugging tests
  testTimeout: 120000, // 2 minutes for complex flow scenarios

  // Coverage configuration
  collectCoverageFrom: [
    '../../backend/**/flow-registry.js',
    '../../backend/**/chain-health-monitor.js',
    '../../backend/**/chain-impact-analyzer.js',
    '../../backend/**/error-dna/**/*.js',
    '../../backend/**/middleware/errorHandler.js',
    '!**/node_modules/**',
    '!**/coverage/**',
    '!**/tests/**'
  ],

  // Enhanced coverage reporting
  coverageReporters: ['text', 'lcov', 'html', 'json-summary', 'clover'],
  coverageDirectory: './coverage',

  // Strict coverage thresholds for flow-aware components
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90
    },
    // Flow-specific components require higher coverage
    '../../backend/**/flow-registry.js': {
      branches: 95,
      functions: 100,
      lines: 95,
      statements: 95
    },
    '../../backend/**/chain-health-monitor.js': {
      branches: 95,
      functions: 100,
      lines: 95,
      statements: 95
    }
  },

  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/setup/jest.setup.js',
    '<rootDir>/setup/mocks.setup.js'
  ],

  // Global setup and teardown
  globalSetup: '<rootDir>/setup/global.setup.js',
  globalTeardown: '<rootDir>/setup/global.teardown.js',

  // Performance optimization
  maxWorkers: '75%',
  workerIdleMemoryLimit: '1GB',

  // Module mapping
  moduleNameMapping: {
    '^@flow-aware/(.*)$': '<rootDir>/$1',
    '^@mocks/(.*)$': '<rootDir>/mocks/$1',
    '^@utils/(.*)$': '<rootDir>/utils/$1',
    '^@backend/(.*)$': '<rootDir>/../../backend/$1'
  },

  // Enhanced reporters for flow-aware testing
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: '<rootDir>/reports',
      filename: 'flow-aware-test-report.html',
      expand: true,
      pageTitle: 'Flow-Aware Error Handling Test Report'
    }],
    ['jest-junit', {
      outputDirectory: '<rootDir>/reports',
      outputName: 'flow-aware-junit.xml',
      suiteName: 'Flow-Aware Error Handling Tests'
    }],
    ['@jest/reporters/CoverageReporter'],
    ['jest-performance-reporter', {
      outputFile: '<rootDir>/reports/performance-report.json'
    }]
  ],

  // Mock configuration
  clearMocks: true,
  restoreMocks: true,
  resetMocks: true,

  // Test environment options
  testEnvironmentOptions: {
    NODE_ENV: 'test',
    FLOW_DEBUG: 'true',
    CHAOS_TESTING: 'enabled'
  },

  // Verbose output for debugging
  verbose: true,

  // Cache configuration
  cacheDirectory: '<rootDir>/.jest-cache',

  // Test categories for CI/CD
  projects: [
    {
      displayName: 'Unit Tests',
      testMatch: ['<rootDir>/unit/**/*.test.js'],
      testTimeout: 30000
    },
    {
      displayName: 'Integration Tests',
      testMatch: ['<rootDir>/integration/**/*.test.js'],
      testTimeout: 60000
    },
    {
      displayName: 'End-to-End Tests',
      testMatch: ['<rootDir>/e2e/**/*.test.js'],
      testTimeout: 120000
    },
    {
      displayName: 'Performance Tests',
      testMatch: ['<rootDir>/performance/**/*.test.js'],
      testTimeout: 180000
    },
    {
      displayName: 'Chaos Tests',
      testMatch: ['<rootDir>/chaos/**/*.test.js'],
      testTimeout: 300000
    }
  ]
};