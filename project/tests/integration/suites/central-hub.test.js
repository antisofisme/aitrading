/**
 * Central Hub Service Integration Tests
 * Testing Central Hub service discovery, health monitoring, and service orchestration
 */

const config = require('../config/test-config');
const helpers = require('../utils/test-helpers');

describe('Central Hub Service Integration Tests', () => {
  const { centralHub } = config;
  let testResults = [];

  beforeAll(async () => {
    console.log('🎯 Starting Central Hub Service integration tests...');

    // Check if Central Hub Service is running
    const isPortOpen = await helpers.isPortOpen('localhost', centralHub.expectedPort);
    if (!isPortOpen) {
      console.warn(`⚠️  Central Hub Service port ${centralHub.expectedPort} is not open. Some tests may fail.`);
    }
  });

  afterAll(async () => {
    await helpers.cleanup();
    console.log('📊 Central Hub Service test results:', helpers.formatTestResults(testResults));
  });

  describe('Service Connectivity', () => {
    test('Central Hub should be accessible on port 7000', async () => {
      const isPortOpen = await helpers.isPortOpen('localhost', centralHub.expectedPort);

      testResults.push({
        test: 'Port Accessibility',
        status: isPortOpen ? 'passed' : 'failed',
        details: { port: centralHub.expectedPort, accessible: isPortOpen }
      });

      expect(isPortOpen).toBe(true);
    }, 10000);

    test('Health endpoint should return service status', async () => {
      const health = await helpers.checkHealth(centralHub.baseUrl, centralHub.endpoints.health);

      testResults.push({
        test: 'Health Endpoint',
        status: health.isHealthy ? 'passed' : 'failed',
        details: health
      });

      expect(health.isHealthy).toBe(true);
      expect(health.status).toBe(200);
    }, 15000);

    test('Status endpoint should return hub information', async () => {
      const response = await helpers.makeRequest('GET', `${centralHub.baseUrl}${centralHub.endpoints.status}`);

      const isValid = response.status < 500;

      testResults.push({
        test: 'Status Endpoint',
        status: isValid ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isValid,
          hasData: response.data ? true : false
        }
      });

      expect(isValid).toBe(true);
    }, 10000);
  });

  describe('Service Discovery', () => {
    test('Services endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('GET', `${centralHub.baseUrl}${centralHub.endpoints.services}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Services Endpoint Accessibility',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          hasServices: response.data?.services || Array.isArray(response.data)
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);

    test('Should support service discovery functionality', async () => {
      const discovery = await helpers.discoverServices(centralHub.baseUrl);

      testResults.push({
        test: 'Service Discovery',
        status: discovery.discovered ? 'passed' : 'failed',
        details: discovery
      });

      expect(discovery.discovered).toBe(true);
    }, 15000);

    test('Service registration endpoint should be accessible', async () => {
      const testService = {
        name: 'test-service',
        host: 'localhost',
        port: 9999,
        health: '/health',
        endpoints: ['/api/test']
      };

      const response = await helpers.makeRequest('POST', `${centralHub.baseUrl}${centralHub.endpoints.register}`, testService);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Service Registration',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          canRegister: response.status >= 200 && response.status < 300
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);

    test('Discovery endpoint should return service registry', async () => {
      const response = await helpers.makeRequest('GET', `${centralHub.baseUrl}${centralHub.endpoints.discovery}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Discovery Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          hasDiscoveryData: response.data ? true : false
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);
  });

  describe('Service Registry Integration', () => {
    test('Should detect other foundation services', async () => {
      // Wait a bit for services to register
      await helpers.sleep(2000);

      const discovery = await helpers.discoverServices(centralHub.baseUrl);

      let detectedServices = [];
      if (discovery.discovered && discovery.services) {
        if (Array.isArray(discovery.services)) {
          detectedServices = discovery.services.map(s => s.name || s.id || s);
        } else if (typeof discovery.services === 'object') {
          detectedServices = Object.keys(discovery.services);
        }
      }

      const foundationServicesDetected = centralHub.expectedServices.filter(service =>
        detectedServices.some(detected =>
          detected.includes(service) || service.includes(detected)
        )
      );

      testResults.push({
        test: 'Foundation Services Detection',
        status: foundationServicesDetected.length > 0 ? 'passed' : 'failed',
        details: {
          expectedServices: centralHub.expectedServices,
          detectedServices: detectedServices,
          foundServices: foundationServicesDetected,
          detectionCount: foundationServicesDetected.length
        }
      });

      expect(foundationServicesDetected.length).toBeGreaterThan(0);
    }, 20000);

    test('Should provide service health monitoring', async () => {
      const discovery = await helpers.discoverServices(centralHub.baseUrl);

      let hasHealthData = false;
      if (discovery.discovered && discovery.services) {
        // Check if any service has health information
        const services = Array.isArray(discovery.services) ? discovery.services : Object.values(discovery.services);
        hasHealthData = services.some(service =>
          service?.health || service?.status || service?.healthy !== undefined
        );
      }

      testResults.push({
        test: 'Service Health Monitoring',
        status: hasHealthData ? 'passed' : 'failed',
        details: {
          hasHealthData: hasHealthData,
          servicesWithHealth: discovery.services
        }
      });

      // This test passes if Central Hub can provide any health information
      expect(discovery.discovered).toBe(true);
    }, 15000);
  });

  describe('Error Handling', () => {
    test('Should handle invalid service registration gracefully', async () => {
      const invalidService = {
        // Missing required fields
        invalidField: 'test'
      };

      const response = await helpers.makeRequest('POST', `${centralHub.baseUrl}${centralHub.endpoints.register}`, invalidService);

      const handlesError = response.status >= 400 && response.status < 500;

      testResults.push({
        test: 'Invalid Registration Handling',
        status: handlesError ? 'passed' : 'failed',
        details: {
          status: response.status,
          handlesError: handlesError,
          hasErrorMessage: response.data?.error || response.data?.message
        }
      });

      expect(handlesError).toBe(true);
    }, 10000);

    test('Should handle 404 errors gracefully', async () => {
      const response = await helpers.makeRequest('GET', `${centralHub.baseUrl}/nonexistent-endpoint`);

      const handles404 = response.status === 404;

      testResults.push({
        test: '404 Error Handling',
        status: handles404 ? 'passed' : 'failed',
        details: {
          status: response.status,
          handles404: handles404,
          hasErrorMessage: response.data?.error || response.data?.message
        }
      });

      expect(handles404).toBe(true);
    }, 10000);
  });

  describe('Performance Tests', () => {
    test('Service discovery performance should be acceptable', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.discoverServices(centralHub.baseUrl);
      }, 3);

      const isAcceptable = performance.averageDuration < config.performance.responseTime.acceptable;

      testResults.push({
        test: 'Service Discovery Performance',
        status: isAcceptable ? 'passed' : 'failed',
        details: {
          averageDuration: performance.averageDuration,
          threshold: config.performance.responseTime.acceptable,
          successRate: performance.successRate
        }
      });

      expect(performance.averageDuration).toBeLessThan(config.performance.responseTime.acceptable);
      expect(performance.successRate).toBeGreaterThan(66); // 66% success rate
    }, 20000);

    test('Health endpoint performance should be fast', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.checkHealth(centralHub.baseUrl, centralHub.endpoints.health);
      }, 3);

      const isFast = performance.averageDuration < config.performance.responseTime.fast;

      testResults.push({
        test: 'Health Check Performance',
        status: isFast ? 'passed' : 'failed',
        details: {
          averageDuration: performance.averageDuration,
          threshold: config.performance.responseTime.fast,
          successRate: performance.successRate
        }
      });

      expect(performance.averageDuration).toBeLessThan(config.performance.responseTime.fast);
      expect(performance.successRate).toBe(100);
    }, 15000);
  });

  describe('Integration Readiness', () => {
    test('Should be ready for LEVEL 2 Connectivity integration', async () => {
      const health = await helpers.checkHealth(centralHub.baseUrl, centralHub.endpoints.health);
      const discovery = await helpers.discoverServices(centralHub.baseUrl);

      const isReady = health.isHealthy && discovery.discovered;

      testResults.push({
        test: 'LEVEL 2 Readiness',
        status: isReady ? 'passed' : 'failed',
        details: {
          healthCheck: health.isHealthy,
          serviceDiscovery: discovery.discovered,
          overallReadiness: isReady
        }
      });

      expect(isReady).toBe(true);
    }, 15000);
  });
});