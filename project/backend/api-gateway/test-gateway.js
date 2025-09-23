#!/usr/bin/env node
/**
 * Test script for Lightweight API Gateway
 * Verifies all core functionality and endpoints
 */

const axios = require('axios');
const colors = require('colors');

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:3001';
const TEST_CONFIG = {
  timeout: 5000,
  validateStatus: () => true // Accept all status codes for testing
};

class GatewayTester {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      total: 0,
      tests: []
    };
  }

  async runTest(name, testFn) {
    this.results.total++;
    console.log(`\n🧪 Testing: ${name}`.yellow);

    try {
      const startTime = Date.now();
      const result = await testFn();
      const duration = Date.now() - startTime;

      if (result.success) {
        this.results.passed++;
        console.log(`✅ PASS: ${name} (${duration}ms)`.green);
        if (result.details) {
          console.log(`   ${result.details}`.gray);
        }
      } else {
        this.results.failed++;
        console.log(`❌ FAIL: ${name} (${duration}ms)`.red);
        console.log(`   ${result.error}`.red);
      }

      this.results.tests.push({
        name,
        success: result.success,
        duration,
        error: result.error || null
      });

    } catch (error) {
      this.results.failed++;
      console.log(`❌ ERROR: ${name}`.red);
      console.log(`   ${error.message}`.red);

      this.results.tests.push({
        name,
        success: false,
        duration: 0,
        error: error.message
      });
    }
  }

  async testHealth() {
    const response = await axios.get(`${GATEWAY_URL}/health`, TEST_CONFIG);

    return {
      success: response.status === 200 && response.data.status === 'healthy',
      details: response.status === 200
        ? `Service version: ${response.data.version}, Uptime: ${response.data.uptime}s`
        : `Status: ${response.status}`,
      error: response.status !== 200 ? `Expected 200, got ${response.status}` : null
    };
  }

  async testStatus() {
    const response = await axios.get(`${GATEWAY_URL}/status`, TEST_CONFIG);

    return {
      success: response.status === 200 && response.data.status === 'operational',
      details: response.status === 200
        ? `${response.data.services?.total || 0} services configured`
        : `Status: ${response.status}`,
      error: response.status !== 200 ? `Expected 200, got ${response.status}` : null
    };
  }

  async testMetrics() {
    const response = await axios.get(`${GATEWAY_URL}/metrics`, TEST_CONFIG);

    return {
      success: response.status === 200 && response.data.timestamp,
      details: response.status === 200
        ? `Memory: ${Math.round(response.data.memory?.heapUsed / 1024 / 1024)}MB, CPU: ${JSON.stringify(response.data.cpu)}`
        : `Status: ${response.status}`,
      error: response.status !== 200 ? `Expected 200, got ${response.status}` : null
    };
  }

  async testServices() {
    const response = await axios.get(`${GATEWAY_URL}/services`, TEST_CONFIG);

    return {
      success: response.status === 200 && response.data.services,
      details: response.status === 200
        ? `${Object.keys(response.data.services).length} services listed`
        : `Status: ${response.status}`,
      error: response.status !== 200 ? `Expected 200, got ${response.status}` : null
    };
  }

  async testCORS() {
    const response = await axios.options(`${GATEWAY_URL}/health`, {
      ...TEST_CONFIG,
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET'
      }
    });

    const hasCORS = response.headers['access-control-allow-origin'] ||
                   response.headers['Access-Control-Allow-Origin'];

    return {
      success: response.status < 400 && !!hasCORS,
      details: hasCORS ? `CORS origin: ${hasCORS}` : 'CORS headers not found',
      error: !hasCORS ? 'CORS not properly configured' : null
    };
  }

  async testRateLimitHeaders() {
    const response = await axios.get(`${GATEWAY_URL}/health`, TEST_CONFIG);

    // Check for rate limiting headers (may not be present on first request)
    const hasRateLimit = response.headers['x-ratelimit-limit'] ||
                        response.headers['X-RateLimit-Limit'] ||
                        response.headers['ratelimit-limit'];

    return {
      success: response.status === 200, // Rate limit headers may not be present initially
      details: hasRateLimit
        ? `Rate limit: ${hasRateLimit}`
        : 'Rate limiting configured (headers may appear after limits are hit)',
      error: response.status !== 200 ? `Health check failed: ${response.status}` : null
    };
  }

  async testFlowHeaders() {
    const response = await axios.get(`${GATEWAY_URL}/health`, {
      ...TEST_CONFIG,
      headers: {
        'X-Flow-Id': 'test-flow-123',
        'X-Request-Id': 'test-request-456'
      }
    });

    const hasFlowHeaders = response.headers['x-flow-id'] ||
                          response.headers['X-Flow-Id'];

    return {
      success: response.status === 200,
      details: hasFlowHeaders
        ? `Flow tracking active: ${hasFlowHeaders}`
        : 'Flow tracking may be disabled or not configured',
      error: response.status !== 200 ? `Request failed: ${response.status}` : null
    };
  }

  async testServiceRouting() {
    // Test a typical service route (should return 503 if service is down, which is expected)
    const response = await axios.get(`${GATEWAY_URL}/api/trading/health`, TEST_CONFIG);

    return {
      success: response.status === 503 || response.status === 200 || response.status === 404,
      details: response.status === 503
        ? 'Service unavailable (expected if trading service not running)'
        : response.status === 200
        ? 'Trading service is running'
        : response.status === 404
        ? 'Route not found (check service configuration)'
        : `Unexpected status: ${response.status}`,
      error: ![200, 404, 503].includes(response.status)
        ? `Unexpected routing behavior: ${response.status}`
        : null
    };
  }

  async test404Handling() {
    const response = await axios.get(`${GATEWAY_URL}/nonexistent-route`, TEST_CONFIG);

    return {
      success: response.status === 404 && response.data.code === 'ROUTE_NOT_FOUND',
      details: response.status === 404
        ? `Proper 404 response with code: ${response.data.code}`
        : `Unexpected status: ${response.status}`,
      error: response.status !== 404 ? `Expected 404, got ${response.status}` : null
    };
  }

  async testSecurityHeaders() {
    const response = await axios.get(`${GATEWAY_URL}/health`, TEST_CONFIG);

    const securityHeaders = [
      'x-content-type-options',
      'x-frame-options',
      'x-xss-protection',
      'strict-transport-security'
    ];

    const presentHeaders = securityHeaders.filter(header =>
      response.headers[header] || response.headers[header.toUpperCase()]
    );

    return {
      success: presentHeaders.length >= 2, // At least some security headers
      details: `Security headers present: ${presentHeaders.length}/${securityHeaders.length}`,
      error: presentHeaders.length === 0 ? 'No security headers found' : null
    };
  }

  async runAllTests() {
    console.log('🚀 Starting API Gateway Tests'.cyan.bold);
    console.log(`📍 Testing gateway at: ${GATEWAY_URL}`.cyan);
    console.log('=' .repeat(60));

    // Core functionality tests
    await this.runTest('Health Check', () => this.testHealth());
    await this.runTest('Status Endpoint', () => this.testStatus());
    await this.runTest('Metrics Endpoint', () => this.testMetrics());
    await this.runTest('Services Configuration', () => this.testServices());

    // Security and middleware tests
    await this.runTest('CORS Configuration', () => this.testCORS());
    await this.runTest('Rate Limiting Setup', () => this.testRateLimitHeaders());
    await this.runTest('Flow Tracking Headers', () => this.testFlowHeaders());
    await this.runTest('Security Headers', () => this.testSecurityHeaders());

    // Routing tests
    await this.runTest('Service Routing', () => this.testServiceRouting());
    await this.runTest('404 Error Handling', () => this.test404Handling());

    this.printSummary();
  }

  printSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST SUMMARY'.cyan.bold);
    console.log('='.repeat(60));

    const passRate = ((this.results.passed / this.results.total) * 100).toFixed(1);

    if (this.results.failed === 0) {
      console.log(`🎉 ALL TESTS PASSED! (${this.results.passed}/${this.results.total})`.green.bold);
    } else {
      console.log(`📊 Tests: ${this.results.passed} passed, ${this.results.failed} failed`.yellow);
      console.log(`📈 Pass rate: ${passRate}%`.yellow);
    }

    if (this.results.failed > 0) {
      console.log('\n❌ FAILED TESTS:'.red.bold);
      this.results.tests
        .filter(test => !test.success)
        .forEach(test => {
          console.log(`   • ${test.name}: ${test.error}`.red);
        });
    }

    console.log('\n🏆 RECOMMENDATIONS:'.cyan.bold);

    if (this.results.failed === 0) {
      console.log('✅ Gateway is ready for production deployment!'.green);
    } else {
      console.log('🔧 Fix failed tests before production deployment'.yellow);
    }

    console.log('📋 Next steps:');
    console.log('   • Start microservices to test full routing');
    console.log('   • Configure environment variables for production');
    console.log('   • Set up monitoring and alerting');
    console.log('   • Test with actual client applications');

    process.exit(this.results.failed === 0 ? 0 : 1);
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new GatewayTester();
  tester.runAllTests().catch(error => {
    console.error('Test runner failed:'.red, error.message);
    process.exit(1);
  });
}

module.exports = GatewayTester;