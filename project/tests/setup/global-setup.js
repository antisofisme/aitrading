/**
 * Global Test Setup
 * Runs once before all tests
 */

module.exports = async () => {
  console.log('🚀 Initializing AI Pipeline Test Environment...\n');

  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error'; // Reduce log noise during tests

  // Mock environment variables for testing
  process.env.MT5_LOGIN = 'test_login';
  process.env.MT5_PASSWORD = 'test_password';
  process.env.MT5_SERVER = 'test_server';
  process.env.OPENAI_API_KEY = 'test_openai_key';
  process.env.ANTHROPIC_API_KEY = 'test_anthropic_key';

  // Initialize global test utilities
  global.testStartTime = Date.now();

  // Create test directories if they don't exist
  const fs = require('fs');
  const path = require('path');

  const testDirs = [
    path.join(__dirname, '../../coverage'),
    path.join(__dirname, '../../test-results'),
    path.join(__dirname, '../../test-artifacts')
  ];

  testDirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });

  // Performance baseline setup
  global.performanceBaseline = {
    aiDecisionLatency: 15, // ms
    dataProcessingLatency: 50, // ms
    throughput: 50, // operations per second
    memoryThreshold: 500 * 1024 * 1024 // 500MB
  };

  console.log('✅ Global test setup completed\n');
};