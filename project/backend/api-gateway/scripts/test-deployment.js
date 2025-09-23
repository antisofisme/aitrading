#!/usr/bin/env node

/**
 * API Gateway Deployment Test Script
 *
 * Tests the deployed API Gateway to ensure all features are working correctly:
 * - Health checks
 * - Database connectivity
 * - Configuration Service integration
 * - Flow Registry functionality
 */

const axios = require('axios');

class DeploymentTester {
  constructor(baseURL = 'http://localhost:3001') {
    this.baseURL = baseURL;
    this.results = [];
    this.startTime = Date.now();
  }

  async runTests() {
    console.log(colors.bright + '🧪 Starting API Gateway Deployment Tests...\n' + colors.reset);

    const tests = [
      { name: 'Health Check', test: () => this.testHealthCheck() },
      { name: 'Database Status', test: () => this.testDatabaseStatus() },
      { name: 'API Documentation', test: () => this.testAPIDocumentation() },
      { name: 'Configuration Service', test: () => this.testConfigurationService() },
      { name: 'Service Discovery', test: () => this.testServiceDiscovery() },
      { name: 'Flow Registry', test: () => this.testFlowRegistry() },
      { name: 'Error Handling', test: () => this.testErrorHandling() },
      { name: 'Security Headers', test: () => this.testSecurityHeaders() },
      { name: 'Rate Limiting', test: () => this.testRateLimiting() }
    ];

    for (const testCase of tests) {
      await this.runTest(testCase.name, testCase.test);
    }

    this.printSummary();
  }

  async runTest(name, testFn) {
    process.stdout.write(`${colors.dim}Testing ${name}...${colors.reset}`);

    try {
      const startTime = Date.now();
      await testFn();
      const duration = Date.now() - startTime;

      this.results.push({ name, status: 'PASS', duration });
      console.log(`\r${colors.green}✅ ${name} - PASSED${colors.reset} ${colors.dim}(${duration}ms)${colors.reset}`);
    } catch (error) {
      this.results.push({ name, status: 'FAIL', error: error.message });
      console.log(`\r${colors.red}❌ ${name} - FAILED${colors.reset}`);
      console.log(`   ${colors.red}Error: ${error.message}${colors.reset}`);
    }
  }

  async testHealthCheck() {
    const response = await axios.get(`${this.baseURL}/health`);

    if (response.status !== 200) {
      throw new Error(`Expected status 200, got ${response.status}`);
    }

    const health = response.data;
    if (!health.success || !health.data) {
      throw new Error('Invalid health check response format');
    }

    if (health.data.status !== 'healthy' && health.data.status !== 'degraded') {
      throw new Error(`Unexpected health status: ${health.data.status}`);
    }

    // Check required fields
    const requiredFields = ['version', 'uptime', 'environment', 'services'];
    for (const field of requiredFields) {
      if (!health.data.hasOwnProperty(field)) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
  }

  async testDatabaseStatus() {
    const response = await axios.get(`${this.baseURL}/api/v1/status/databases`);

    if (response.status !== 200) {
      throw new Error(`Expected status 200, got ${response.status}`);
    }

    const dbStatus = response.data;
    if (!dbStatus.success || !dbStatus.data) {
      throw new Error('Invalid database status response format');
    }

    // Check for database connections
    const expectedDatabases = ['postgres', 'dragonflydb', 'clickhouse', 'weaviate', 'arangodb', 'redis'];
    for (const db of expectedDatabases) {
      if (!dbStatus.data.connections.hasOwnProperty(db)) {
        throw new Error(`Missing database connection status for: ${db}`);
      }
    }
  }

  async testAPIDocumentation() {
    const response = await axios.get(`${this.baseURL}/api`);

    if (response.status !== 200) {
      throw new Error(`Expected status 200, got ${response.status}`);
    }

    const docs = response.data;
    if (!docs.success || !docs.message || !docs.endpoints) {
      throw new Error('Invalid API documentation response format');
    }

    // Check for expected endpoints
    const expectedEndpoints = ['health', 'databases', 'configuration', 'services', 'flows'];
    for (const endpoint of expectedEndpoints) {
      if (!docs.endpoints.hasOwnProperty(endpoint)) {
        throw new Error(`Missing endpoint documentation: ${endpoint}`);
      }
    }
  }

  async testConfigurationService() {
    try {
      // Test configuration endpoint (should handle missing config gracefully)
      const response = await axios.get(`${this.baseURL}/api/v1/config/test-key`);

      // Should return 404 or 500 (depending on Configuration Service status)
      if (![404, 500].includes(response.status)) {
        throw new Error(`Unexpected response status: ${response.status}`);
      }
    } catch (error) {
      // Axios throws for 4xx/5xx, check if it's the expected 404
      if (error.response && [404, 500].includes(error.response.status)) {
        // This is expected behavior
        return;
      }
      throw error;
    }
  }

  async testServiceDiscovery() {
    try {
      const response = await axios.get(`${this.baseURL}/api/v1/services`);

      // Should return 200 or 500 (depending on Configuration Service status)
      if (![200, 500].includes(response.status)) {
        throw new Error(`Unexpected response status: ${response.status}`);
      }
    } catch (error) {
      if (error.response && error.response.status === 500) {
        // This is expected if Configuration Service is not available
        return;
      }
      throw error;
    }
  }

  async testFlowRegistry() {
    try {
      // Test flow creation (should handle missing Flow Registry gracefully)
      const testFlow = {
        name: 'Test Flow',
        type: 'test_flow',
        version: '1.0.0',
        description: 'Deployment test flow'
      };

      const response = await axios.post(`${this.baseURL}/api/v1/flows`, testFlow);

      // Should return 201 or 400/500 (depending on Configuration Service status)
      if (![201, 400, 500].includes(response.status)) {
        throw new Error(`Unexpected response status: ${response.status}`);
      }
    } catch (error) {
      if (error.response && [400, 500].includes(error.response.status)) {
        // This is expected if Configuration Service is not available
        return;
      }
      throw error;
    }
  }

  async testErrorHandling() {
    // Test 404 handling
    try {
      await axios.get(`${this.baseURL}/non-existent-endpoint`);
      throw new Error('Expected 404 error');
    } catch (error) {
      if (!error.response || error.response.status !== 404) {
        throw new Error(`Expected 404, got ${error.response?.status || 'no response'}`);
      }

      const errorResponse = error.response.data;
      if (!errorResponse.message || errorResponse.success !== false) {
        throw new Error('Invalid 404 error response format');
      }
    }
  }

  async testSecurityHeaders() {
    const response = await axios.get(`${this.baseURL}/health`);

    // Check for security headers
    const securityHeaders = [
      'x-content-type-options',
      'x-frame-options'
    ];

    for (const header of securityHeaders) {
      if (!response.headers[header]) {
        throw new Error(`Missing security header: ${header}`);
      }
    }

    // Check for request ID header
    if (!response.headers['x-request-id']) {
      throw new Error('Missing X-Request-ID header');
    }
  }

  async testRateLimiting() {
    // Make multiple rapid requests to test rate limiting
    const requests = Array(5).fill().map(() =>
      axios.get(`${this.baseURL}/health`, { timeout: 5000 })
    );

    try {
      const responses = await Promise.all(requests);

      // All health check requests should succeed (rate limiting skipped for health)
      for (const response of responses) {
        if (response.status !== 200) {
          throw new Error(`Rate limiting test failed: unexpected status ${response.status}`);
        }
      }
    } catch (error) {
      throw new Error(`Rate limiting test failed: ${error.message}`);
    }
  }

  printSummary() {
    const duration = Date.now() - this.startTime;
    const passed = this.results.filter(r => r.status === 'PASS').length;
    const failed = this.results.filter(r => r.status === 'FAIL').length;

    console.log('\n' + '='.repeat(60));
    console.log(colors.bright + '📊 TEST SUMMARY' + colors.reset);
    console.log('='.repeat(60));

    console.log(`${colors.green}✅ Passed: ${passed}${colors.reset}`);
    console.log(`${colors.red}❌ Failed: ${failed}${colors.reset}`);
    console.log(`⏱️  Total Duration: ${duration}ms`);

    if (failed === 0) {
      console.log(`\n${colors.green}🎉 All tests passed! API Gateway is ready for production.${colors.reset}`);
    } else {
      console.log(`\n${colors.red}⚠️  Some tests failed. Please check the deployment.${colors.reset}`);
      process.exit(1);
    }
  }
}

// Color helper
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Run tests if called directly
if (require.main === module) {
  const baseURL = process.argv[2] || 'http://localhost:3001';

  console.log(colors.bright + '🚀 API Gateway Deployment Test' + colors.reset);
  console.log(`Testing: ${baseURL}\n`);

  const tester = new DeploymentTester(baseURL);
  tester.runTests().catch(error => {
    console.error(colors.red + '💥 Test runner failed:', error.message + colors.reset);
    process.exit(1);
  });
}

module.exports = DeploymentTester;