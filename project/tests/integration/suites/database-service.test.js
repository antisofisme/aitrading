/**
 * Database Service Integration Tests
 * Testing multi-database connections and database service functionality
 */

const config = require('../config/test-config');
const helpers = require('../utils/test-helpers');

describe('Database Service Integration Tests', () => {
  const { databaseService } = config;
  let testResults = [];

  beforeAll(async () => {
    console.log('🗄️  Starting Database Service integration tests...');

    // Check if Database Service is running
    const isPortOpen = await helpers.isPortOpen('localhost', databaseService.expectedPort);
    if (!isPortOpen) {
      console.warn(`⚠️  Database Service port ${databaseService.expectedPort} is not open. Some tests may fail.`);
    }
  });

  afterAll(async () => {
    await helpers.cleanup();
    console.log('📊 Database Service test results:', helpers.formatTestResults(testResults));
  });

  describe('Service Connectivity', () => {
    test('Database Service should be accessible on port 8008', async () => {
      const isPortOpen = await helpers.isPortOpen('localhost', databaseService.expectedPort);

      testResults.push({
        test: 'Port Accessibility',
        status: isPortOpen ? 'passed' : 'failed',
        details: { port: databaseService.expectedPort, accessible: isPortOpen }
      });

      expect(isPortOpen).toBe(true);
    }, 10000);

    test('Health endpoint should return service status', async () => {
      const health = await helpers.checkHealth(databaseService.baseUrl, databaseService.endpoints.health);

      testResults.push({
        test: 'Health Endpoint',
        status: health.isHealthy ? 'passed' : 'failed',
        details: health
      });

      expect(health.isHealthy).toBe(true);
      expect(health.status).toBe(200);
    }, 15000);

    test('Service info endpoint should return service details', async () => {
      const response = await helpers.makeRequest('GET', `${databaseService.baseUrl}${databaseService.endpoints.info}`);

      const isValid = response.status === 200 && response.data?.service === 'Database Service';

      testResults.push({
        test: 'Service Info',
        status: isValid ? 'passed' : 'failed',
        details: {
          status: response.status,
          service: response.data?.service,
          version: response.data?.version,
          port: response.data?.port
        }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('service', 'Database Service');
      expect(response.data).toHaveProperty('version');
      expect(response.data).toHaveProperty('port');
      expect(response.data).toHaveProperty('status', 'running');
    }, 10000);
  });

  describe('Multi-Database Connections', () => {
    test('Main database connection should be functional', async () => {
      const dbTest = await helpers.testDatabaseConnection(databaseService.databases.main, 'main');

      testResults.push({
        test: 'Main Database Connection',
        status: dbTest.connected ? 'passed' : 'failed',
        details: dbTest
      });

      expect(dbTest.connected).toBe(true);
      expect(dbTest).toHaveProperty('currentTime');
      expect(dbTest).toHaveProperty('version');
    }, 15000);

    test('Auth database connection should be functional', async () => {
      const dbTest = await helpers.testDatabaseConnection(databaseService.databases.auth, 'auth');

      testResults.push({
        test: 'Auth Database Connection',
        status: dbTest.connected ? 'passed' : 'failed',
        details: dbTest
      });

      expect(dbTest.connected).toBe(true);
      expect(dbTest).toHaveProperty('currentTime');
      expect(dbTest).toHaveProperty('version');
    }, 15000);

    test('Trading database connection should be functional', async () => {
      const dbTest = await helpers.testDatabaseConnection(databaseService.databases.trading, 'trading');

      testResults.push({
        test: 'Trading Database Connection',
        status: dbTest.connected ? 'passed' : 'failed',
        details: dbTest
      });

      expect(dbTest.connected).toBe(true);
      expect(dbTest).toHaveProperty('currentTime');
      expect(dbTest).toHaveProperty('version');
    }, 15000);

    test('Market database connection should be functional', async () => {
      const dbTest = await helpers.testDatabaseConnection(databaseService.databases.market, 'market');

      testResults.push({
        test: 'Market Database Connection',
        status: dbTest.connected ? 'passed' : 'failed',
        details: dbTest
      });

      expect(dbTest.connected).toBe(true);
      expect(dbTest).toHaveProperty('currentTime');
      expect(dbTest).toHaveProperty('version');
    }, 15000);

    test('Analytics database connection should be functional', async () => {
      const dbTest = await helpers.testDatabaseConnection(databaseService.databases.analytics, 'analytics');

      testResults.push({
        test: 'Analytics Database Connection',
        status: dbTest.connected ? 'passed' : 'failed',
        details: dbTest
      });

      expect(dbTest.connected).toBe(true);
      expect(dbTest).toHaveProperty('currentTime');
      expect(dbTest).toHaveProperty('version');
    }, 15000);
  });

  describe('Database Service API', () => {
    test('Query endpoint should be accessible', async () => {
      const testQuery = {
        query: 'SELECT NOW() as current_time',
        params: []
      };

      const response = await helpers.makeRequest('POST', `${databaseService.baseUrl}${databaseService.endpoints.query}`, testQuery);

      const isSuccessful = response.status === 200 && response.data?.success === true;

      testResults.push({
        test: 'Query Endpoint',
        status: isSuccessful ? 'passed' : 'failed',
        details: {
          status: response.status,
          successful: isSuccessful,
          hasData: response.data?.data ? true : false
        }
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success', true);
      expect(response.data).toHaveProperty('data');
    }, 15000);

    test('Users endpoint should be accessible', async () => {
      // Test creating a user
      const testUser = {
        email: config.testData.testUser.email,
        password: config.testData.testUser.password,
        name: config.testData.testUser.name
      };

      const response = await helpers.makeRequest('POST', `${databaseService.baseUrl}${databaseService.endpoints.users}`, testUser);

      const isAccessible = response.status < 500; // Any response except server error

      testResults.push({
        test: 'Users Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          canCreateUser: response.status === 201
        }
      });

      expect(isAccessible).toBe(true);
    }, 15000);

    test('Migration endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('POST', `${databaseService.baseUrl}${databaseService.endpoints.migrate}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Migration Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible
        }
      });

      expect(isAccessible).toBe(true);
    }, 20000);
  });

  describe('Performance Tests', () => {
    test('Database query performance should be acceptable', async () => {
      const performance = await helpers.measurePerformance(async () => {
        const testQuery = {
          query: 'SELECT 1 as test_value',
          params: []
        };
        await helpers.makeRequest('POST', `${databaseService.baseUrl}${databaseService.endpoints.query}`, testQuery);
      }, 5);

      const isPerformant = performance.averageDuration < config.performance.responseTime.acceptable;

      testResults.push({
        test: 'Database Query Performance',
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
      expect(performance.successRate).toBeGreaterThan(80); // 80% success rate for DB operations
    }, 30000);

    test('Health check performance should be fast', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.checkHealth(databaseService.baseUrl, databaseService.endpoints.health);
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
    }, 20000);
  });
});