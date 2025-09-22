module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Test file patterns
  testMatch: [
    '**/tests/**/*.test.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage settings
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Files to include in coverage
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/app.js', // Exclude main app file
    '!src/config/**', // Exclude config files
    '!**/node_modules/**',
    '!**/logs/**',
    '!**/coverage/**'
  ],

  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup.js'
  ],

  // Module path mapping
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },

  // Test timeout
  testTimeout: 30000,

  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true,

  // Verbose output
  verbose: true,

  // Force exit after tests
  forceExit: true,

  // Detect open handles
  detectOpenHandles: true,

  // Transform settings
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/logs/',
    '/coverage/'
  ],

  // Module file extensions
  moduleFileExtensions: [
    'js',
    'json'
  ],

  // Global variables
  globals: {
    'NODE_ENV': 'test'
  },

  // Mock patterns
  moduleNameMapping: {
    '^@config/(.*)$': '<rootDir>/src/config/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@models/(.*)$': '<rootDir>/src/models/$1',
    '^@middleware/(.*)$': '<rootDir>/src/middleware/$1',
    '^@controllers/(.*)$': '<rootDir>/src/controllers/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1'
  }
};