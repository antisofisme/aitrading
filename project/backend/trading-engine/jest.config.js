module.exports = {
  // Test environment
  testEnvironment: 'node',
  
  // Root directory
  rootDir: '.',
  
  // Test directories
  testMatch: [
    '<rootDir>/tests/**/*.test.js',
    '<rootDir>/src/**/*.test.js'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/server.js', // Exclude server startup file
    '!src/utils/logger.js' // Exclude logger (hard to test)
  ],
  
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/services/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup.js'
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Mock patterns
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Verbose output
  verbose: true,
  
  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(some-es6-package)/)'  
  ],
  
  // Global setup/teardown
  globalSetup: '<rootDir>/tests/globalSetup.js',
  globalTeardown: '<rootDir>/tests/globalTeardown.js'
};