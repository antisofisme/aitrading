module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>'],
  testMatch: [
    '**/__tests__/**/*.+(ts|tsx|js)',
    '**/*.(test|spec).+(ts|tsx|js)'
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },
  collectCoverageFrom: [
    '../ai_trading/**/*.{js,py}',
    '../src/**/*.{js,ts}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/coverage/**'
  ],
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  coverageDirectory: './coverage',
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/setup/jest.setup.js'],
  testTimeout: 30000,
  maxWorkers: 4,
  // Parallel test execution for performance
  testRunner: 'jest-circus/runner',
  // Mock configuration
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/../src/$1',
    '^@tests/(.*)$': '<rootDir>/$1'
  },
  // Global test environment variables
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  }
};