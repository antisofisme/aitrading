const ErrorDNA = require('../src/index');
const request = require('supertest');

describe('ErrorDNA Integration', () => {
  let errorDNA;
  let app;

  beforeAll(async () => {
    // Initialize ErrorDNA with test configuration
    errorDNA = new ErrorDNA({
      service: {
        port: 0 // Use random port for testing
      },
      storage: {
        baseDir: '/tmp/error-dna-test',
        retentionDays: 1
      },
      notifications: {
        enabled: false // Disable notifications for testing
      },
      integration: {
        centralHub: {
          baseUrl: 'http://localhost:9999', // Non-existent URL for testing
          timeout: 1000
        },
        importManager: {
          baseUrl: 'http://localhost:9998', // Non-existent URL for testing
          timeout: 1000
        }
      }
    });

    await errorDNA.init();
    app = errorDNA.app;
  });

  afterAll(async () => {
    if (errorDNA) {
      await errorDNA.stop();
    }
  });

  describe('API endpoints', () => {
    test('GET /health should return health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body.status).toBeDefined();
      expect(response.body.timestamp).toBeDefined();
      expect(response.body.uptime).toBeDefined();
      expect(response.body.metrics).toBeDefined();
      expect(response.body.components).toBeDefined();
    });

    test('POST /api/errors should process error', async () => {
      const testError = {
        message: 'Test database connection error',
        stack: 'Error: ECONNREFUSED at Database.connect()',
        code: 'ECONNREFUSED',
        type: 'DatabaseError'
      };

      const response = await request(app)
        .post('/api/errors')
        .send({ error: testError, context: { operation: 'database_connect' } })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.errorId).toBeDefined();
      expect(response.body.categorization).toBeDefined();
      expect(response.body.categorization.category).toBe('SYSTEM');
      expect(response.body.patterns).toBeDefined();
    });

    test('GET /api/errors should return stored errors', async () => {
      // First, add an error
      const testError = {
        message: 'Another test error',
        type: 'TestError'
      };

      await request(app)
        .post('/api/errors')
        .send({ error: testError });

      // Then retrieve errors
      const response = await request(app)
        .get('/api/errors')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.errors)).toBe(true);
    });

    test('GET /api/patterns should return detected patterns', async () => {
      const response = await request(app)
        .get('/api/patterns')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.patterns)).toBe(true);
    });

    test('GET /api/metrics should return system metrics', async () => {
      const response = await request(app)
        .get('/api/metrics')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.metrics).toBeDefined();
      expect(response.body.metrics.errorsProcessed).toBeDefined();
      expect(response.body.metrics.uptime).toBeDefined();
    });

    test('POST /api/import-errors should handle import errors', async () => {
      const importError = {
        id: 'import_error_123',
        message: 'CSV parsing failed on line 42',
        code: 'PARSE_ERROR',
        source: 'csv_importer',
        file: 'data.csv',
        lineNumber: 42,
        importId: 'import_456',
        timestamp: new Date().toISOString()
      };

      const response = await request(app)
        .post('/api/import-errors')
        .send(importError)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.processResult).toBeDefined();
    });
  });

  describe('error processing pipeline', () => {
    test('should process error through complete pipeline', async () => {
      const testError = {
        message: 'Trading order execution failed: insufficient funds',
        stack: 'TradingError: Order rejected by exchange',
        code: 'ORDER_REJECTED',
        type: 'TradingError'
      };

      const context = {
        operation: 'place_order',
        userId: 'user123',
        orderId: 'order456'
      };

      const result = await errorDNA.processError(testError, context);

      expect(result.success).toBe(true);
      expect(result.errorId).toBeDefined();
      expect(result.categorization.category).toBe('TRADING');
      expect(result.categorization.severity).toBe('CRITICAL');
      expect(result.patterns).toBeDefined();
      expect(result.processingTime).toBeGreaterThan(0);
    });

    test('should detect patterns across multiple similar errors', async () => {
      const baseError = {
        message: 'API request timeout to external service',
        code: '408',
        type: 'TimeoutError'
      };

      // Process multiple similar errors
      const results = [];
      for (let i = 0; i < 4; i++) {
        const result = await errorDNA.processError({
          ...baseError,
          timestamp: new Date().toISOString()
        });
        results.push(result);
      }

      // Should detect pattern after multiple occurrences
      const hasNewPattern = results.some(r => r.patterns.newPatterns.length > 0);
      const hasExistingPattern = results.some(r => r.patterns.existingPatterns.length > 0);

      expect(hasNewPattern || hasExistingPattern).toBe(true);
    });

    test('should attempt recovery for high severity errors', async () => {
      const criticalError = {
        message: 'Database connection lost',
        code: 'ECONNREFUSED',
        type: 'DatabaseError'
      };

      const context = {
        operation: 'database_query',
        retryFunction: jest.fn().mockResolvedValue({ success: true })
      };

      const result = await errorDNA.processError(criticalError, context);

      expect(result.success).toBe(true);
      expect(result.recovery).toBeDefined();
      expect(result.recovery.strategy).toBeDefined();
    });

    test('should handle processing errors gracefully', async () => {
      // Test with malformed error
      const result = await errorDNA.processError(null);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('storage and retrieval', () => {
    test('should store and retrieve errors with filters', async () => {
      // Process a few different types of errors
      const errors = [
        { message: 'System error 1', type: 'SystemError' },
        { message: 'API error 1', code: '500', type: 'APIError' },
        { message: 'User error 1', code: '400', type: 'UserError' }
      ];

      for (const error of errors) {
        await errorDNA.processError(error);
      }

      // Test retrieval with filters
      const response = await request(app)
        .get('/api/errors?category=SYSTEM')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.errors).toBeDefined();

      // Should only return system errors
      const systemErrors = response.body.errors.filter(e =>
        e.categorization?.category === 'SYSTEM'
      );
      expect(systemErrors.length).toBeGreaterThan(0);
    });

    test('should provide error statistics', async () => {
      const response = await request(app)
        .get('/api/metrics')
        .expect(200);

      expect(response.body.metrics.storage).toBeDefined();
      expect(response.body.metrics.storage.total).toBeGreaterThanOrEqual(0);
      expect(response.body.metrics.storage.byCategory).toBeDefined();
      expect(response.body.metrics.storage.bySeverity).toBeDefined();
    });
  });

  describe('health monitoring', () => {
    test('should provide comprehensive health status', async () => {
      const health = await errorDNA.getHealth();

      expect(health.status).toBeDefined();
      expect(['healthy', 'degraded', 'unhealthy']).toContain(health.status);
      expect(health.timestamp).toBeDefined();
      expect(health.uptime).toBeGreaterThan(0);
      expect(health.metrics).toBeDefined();
      expect(health.components).toBeDefined();

      // Check component health
      expect(health.components.storage).toBeDefined();
      expect(health.components.patternDetector).toBeDefined();
      expect(health.components.recovery).toBeDefined();
      expect(health.components.notifier).toBeDefined();
    });

    test('should monitor integration health', async () => {
      const health = await errorDNA.getHealth();

      expect(health.integrations).toBeDefined();
      // Since we're using non-existent URLs, these should be unhealthy
      if (health.integrations.centralHub) {
        expect(health.integrations.centralHub.status).toBe('unhealthy');
      }
      if (health.integrations.importManager) {
        expect(health.integrations.importManager.status).toBe('unhealthy');
      }
    });
  });

  describe('error handling', () => {
    test('should handle invalid requests gracefully', async () => {
      // Test invalid JSON
      const response = await request(app)
        .post('/api/errors')
        .send('invalid json')
        .expect(500);

      expect(response.body.success).toBe(false);
    });

    test('should handle missing error data', async () => {
      const response = await request(app)
        .post('/api/errors')
        .send({}) // No error field
        .expect(500);

      expect(response.body.success).toBe(false);
    });

    test('should handle API errors with proper status codes', async () => {
      // Test non-existent endpoint
      await request(app)
        .get('/api/nonexistent')
        .expect(404);
    });
  });

  describe('performance', () => {
    test('should process errors within reasonable time', async () => {
      const testError = {
        message: 'Performance test error',
        type: 'TestError'
      };

      const startTime = Date.now();
      const result = await errorDNA.processError(testError);
      const processingTime = Date.now() - startTime;

      expect(result.success).toBe(true);
      expect(processingTime).toBeLessThan(1000); // Should process within 1 second
    });

    test('should handle concurrent error processing', async () => {
      const testErrors = Array.from({ length: 10 }, (_, i) => ({
        message: `Concurrent test error ${i}`,
        type: 'ConcurrentTestError'
      }));

      const startTime = Date.now();
      const promises = testErrors.map(error => errorDNA.processError(error));
      const results = await Promise.all(promises);
      const totalTime = Date.now() - startTime;

      // All should succeed
      expect(results.every(r => r.success)).toBe(true);

      // Should complete within reasonable time
      expect(totalTime).toBeLessThan(5000);

      // Should have processed all errors
      expect(results.length).toBe(testErrors.length);
    });
  });
});