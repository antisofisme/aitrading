/**
 * API Gateway Integration Tests
 * Testing API Gateway service health, connectivity, and basic functionality
 */

const config = require('../config/test-config');
const helpers = require('../utils/test-helpers');

describe('API Gateway Integration Tests', () => {
  const { apiGateway } = config;
  let testResults = [];

  beforeAll(async () => {
    console.log('🔌 Starting API Gateway integration tests...');

    // Check if API Gateway is running
    const isPortOpen = await helpers.isPortOpen('localhost', apiGateway.expectedPort);
    if (!isPortOpen) {
      console.warn(`⚠️  API Gateway port ${apiGateway.expectedPort} is not open. Some tests may fail.`);
    }
  });

  afterAll(async () => {
    await helpers.cleanup();
    console.log('📊 API Gateway test results:', helpers.formatTestResults(testResults));
  });

  describe('Service Connectivity', () => {
    test('API Gateway should be accessible on port 3001', async () => {
      const isPortOpen = await helpers.isPortOpen('localhost', apiGateway.expectedPort);

      testResults.push({
        test: 'Port Accessibility',
        status: isPortOpen ? 'passed' : 'failed',
        details: { port: apiGateway.expectedPort, accessible: isPortOpen }
      });

      expect(isPortOpen).toBe(true);
    }, 10000);

    test('Health endpoint should return 200 status', async () => {
      const health = await helpers.checkHealth(apiGateway.baseUrl, apiGateway.endpoints.health);

      testResults.push({
        test: 'Health Endpoint',
        status: health.isHealthy ? 'passed' : 'failed',
        details: health
      });

      expect(health.isHealthy).toBe(true);
      expect(health.status).toBe(200);
      expect(health.data).toHaveProperty('success', true);
      expect(health.data).toHaveProperty('message');
      expect(health.data).toHaveProperty('timestamp');
    }, 15000);

    test('API documentation endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.api}`);

      const isSuccess = response.status === 200 && response.data.success === true;

      testResults.push({
        test: 'API Documentation',
        status: isSuccess ? 'passed' : 'failed',
        details: {
          status: response.status,
          hasDocumentation: response.data?.documentation ? true : false,
          hasAuthentication: response.data?.authentication ? true : false
        }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success', true);
      expect(response.data).toHaveProperty('documentation');
      expect(response.data).toHaveProperty('authentication');
      expect(response.data).toHaveProperty('defaultCredentials');
    }, 10000);
  });

  describe('Authentication System', () => {
    test('Auth endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.auth}`);

      // Auth endpoint might return 404 for GET, but should be accessible
      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Auth Endpoint Accessibility',
        status: isAccessible ? 'passed' : 'failed',
        details: { status: response.status, accessible: isAccessible }
      });

      expect(isAccessible).toBe(true);
    }, 10000);

    test('Default admin credentials should be configured', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.api}`);

      const hasDefaultCredentials = response.data?.defaultCredentials?.admin ? true : false;

      testResults.push({
        test: 'Default Admin Credentials',
        status: hasDefaultCredentials ? 'passed' : 'failed',
        details: {
          configured: hasDefaultCredentials,
          adminEmail: response.data?.defaultCredentials?.admin?.email
        }
      });

      expect(response.status).toBe(200);
      expect(response.data.defaultCredentials).toHaveProperty('admin');
      expect(response.data.defaultCredentials.admin).toHaveProperty('email');
      expect(response.data.defaultCredentials.admin).toHaveProperty('password');
    }, 10000);
  });

  describe('Central Hub Integration', () => {
    test('Central Hub integration endpoint should be configured', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.integration}`);

      const isConfigured = response.status === 200 && response.data?.success === true;

      testResults.push({
        test: 'Central Hub Integration',
        status: isConfigured ? 'passed' : 'failed',
        details: {
          status: response.status,
          configured: isConfigured,
          hubUrl: response.data?.data?.hubUrl,
          apiKeyConfigured: response.data?.data?.apiKey === '[CONFIGURED]'
        }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success', true);
      expect(response.data.data).toHaveProperty('hubUrl');
      expect(response.data.data).toHaveProperty('status');
    }, 10000);
  });

  describe('Security and Middleware', () => {
    test('CORS headers should be present', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.health}`);

      const hasCorsHeaders = response.headers['access-control-allow-origin'] !== undefined;

      testResults.push({
        test: 'CORS Headers',
        status: hasCorsHeaders ? 'passed' : 'failed',
        details: {
          corsEnabled: hasCorsHeaders,
          allowOrigin: response.headers['access-control-allow-origin']
        }
      });

      expect(hasCorsHeaders).toBe(true);
    }, 10000);

    test('Security headers should be present', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}${apiGateway.endpoints.health}`);

      const hasSecurityHeaders = response.headers['x-frame-options'] !== undefined ||
                                response.headers['x-content-type-options'] !== undefined;

      testResults.push({
        test: 'Security Headers',
        status: hasSecurityHeaders ? 'passed' : 'failed',
        details: {
          frameOptions: response.headers['x-frame-options'],
          contentTypeOptions: response.headers['x-content-type-options'],
          xssProtection: response.headers['x-xss-protection']
        }
      });

      expect(hasSecurityHeaders).toBe(true);
    }, 10000);

    test('Should handle 404 errors gracefully', async () => {
      const response = await helpers.makeRequest('GET', `${apiGateway.baseUrl}/nonexistent-endpoint`);

      const handles404 = response.status === 404 && response.data?.success === false;

      testResults.push({
        test: '404 Error Handling',
        status: handles404 ? 'passed' : 'failed',
        details: {
          status: response.status,
          hasErrorMessage: response.data?.message ? true : false,
          hasErrorCode: response.data?.code ? true : false
        }
      });

      expect(response.status).toBe(404);
      expect(response.data).toHaveProperty('success', false);
      expect(response.data).toHaveProperty('message');
      expect(response.data).toHaveProperty('code');
    }, 10000);
  });

  describe('Performance Tests', () => {
    test('Health endpoint response time should be acceptable', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.checkHealth(apiGateway.baseUrl, apiGateway.endpoints.health);
      }, 5);

      const isPerformant = performance.averageDuration < config.performance.responseTime.acceptable;

      testResults.push({
        test: 'Health Endpoint Performance',
        status: isPerformant ? 'passed' : 'failed',
        details: {
          averageDuration: performance.averageDuration,
          minDuration: performance.minDuration,
          maxDuration: performance.maxDuration,
          successRate: performance.successRate,
          threshold: config.performance.responseTime.acceptable
        }
      });

      expect(performance.averageDuration).toBeLessThan(config.performance.responseTime.acceptable);
      expect(performance.successRate).toBeGreaterThan(95); // 95% success rate
    }, 30000);
  });
});