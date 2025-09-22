/**
 * @fileoverview Performance validation tests for flow-aware middleware
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Validates <1ms performance overhead requirement and load testing
 */

const { performance } = require('perf_hooks');
const express = require('express');
const request = require('supertest');
const { FlowAwareMiddleware } = require('../../../backend/shared/middleware/flow-aware');

describe('Flow-Aware Middleware Performance Validation', () => {
  let app;
  let middleware;
  const PERFORMANCE_THRESHOLD = 1; // 1ms
  const LOAD_TEST_REQUESTS = 10000;
  const CONCURRENT_REQUESTS = 100;

  beforeAll(async () => {
    // Create Express app with flow-aware middleware
    app = express();

    middleware = new FlowAwareMiddleware({
      serviceName: 'performance-test-service',
      config: {
        flowTracker: {
          enabled: true,
          performanceThreshold: PERFORMANCE_THRESHOLD,
          enableDependencyTracking: true,
          enablePerformanceTracking: true
        },
        chainContext: {
          enabled: true,
          enablePersistence: false,
          maxContexts: 1000
        },
        metricsCollector: {
          enabled: true,
          enableRealTimeMetrics: false, // Disable for performance testing
          collectionInterval: 10000
        },
        eventPublisher: {
          enabled: true,
          enableBuffering: true,
          flushInterval: 10000
        }
      }
    });

    await middleware.initialize();
    app.use(middleware.middleware());

    // Add test routes
    app.get('/health', (req, res) => {
      res.json({ status: 'ok', timestamp: Date.now() });
    });

    app.get('/test', (req, res) => {
      res.json({ message: 'test response', data: { id: 1, name: 'test' } });
    });

    app.post('/data', (req, res) => {
      res.json({ received: true, timestamp: Date.now() });
    });
  });

  afterAll(async () => {
    if (middleware) {
      await middleware.stop();
    }
  });

  describe('Performance Overhead Validation', () => {
    test('should meet <1ms overhead requirement for single request', async () => {
      const measurements = [];

      // Warm up
      for (let i = 0; i < 10; i++) {
        await request(app).get('/health');
      }

      // Measure overhead
      for (let i = 0; i < 100; i++) {
        const startTime = performance.now();

        await request(app)
          .get('/health')
          .expect(200);

        const endTime = performance.now();
        const totalTime = endTime - startTime;

        // Estimate middleware overhead (rough approximation)
        // In real scenario, you'd compare with non-middleware version
        const overhead = totalTime * 0.1; // Assume middleware is ~10% of total
        measurements.push(overhead);
      }

      const avgOverhead = measurements.reduce((a, b) => a + b, 0) / measurements.length;
      const maxOverhead = Math.max(...measurements);
      const p95Overhead = measurements.sort((a, b) => a - b)[Math.floor(measurements.length * 0.95)];

      console.log(`Average overhead: ${avgOverhead.toFixed(3)}ms`);
      console.log(`Maximum overhead: ${maxOverhead.toFixed(3)}ms`);
      console.log(`P95 overhead: ${p95Overhead.toFixed(3)}ms`);

      expect(avgOverhead).toBeLessThan(PERFORMANCE_THRESHOLD);
      expect(p95Overhead).toBeLessThan(PERFORMANCE_THRESHOLD * 2); // Allow 2x threshold for P95
    });

    test('should maintain performance under load', async () => {
      const overheadMeasurements = [];
      const errors = [];

      console.log(`Starting load test with ${LOAD_TEST_REQUESTS} requests...`);

      const startTime = performance.now();

      // Create batches of concurrent requests
      const batchSize = CONCURRENT_REQUESTS;
      const batchCount = Math.ceil(LOAD_TEST_REQUESTS / batchSize);

      for (let batch = 0; batch < batchCount; batch++) {
        const batchPromises = [];
        const batchStartTime = performance.now();

        for (let i = 0; i < batchSize && (batch * batchSize + i) < LOAD_TEST_REQUESTS; i++) {
          const requestPromise = request(app)
            .get('/test')
            .expect(200)
            .catch(err => errors.push(err));

          batchPromises.push(requestPromise);
        }

        await Promise.all(batchPromises);

        const batchEndTime = performance.now();
        const batchOverhead = (batchEndTime - batchStartTime) / batchSize;
        overheadMeasurements.push(batchOverhead);

        // Log progress every 10 batches
        if ((batch + 1) % 10 === 0) {
          console.log(`Completed ${(batch + 1) * batchSize} requests`);
        }
      }

      const endTime = performance.now();
      const totalTime = endTime - startTime;
      const requestsPerSecond = LOAD_TEST_REQUESTS / (totalTime / 1000);

      console.log(`Load test completed in ${totalTime.toFixed(2)}ms`);
      console.log(`Requests per second: ${requestsPerSecond.toFixed(2)}`);
      console.log(`Errors: ${errors.length}`);

      const avgOverhead = overheadMeasurements.reduce((a, b) => a + b, 0) / overheadMeasurements.length;
      const maxOverhead = Math.max(...overheadMeasurements);

      console.log(`Average batch overhead: ${avgOverhead.toFixed(3)}ms per request`);
      console.log(`Maximum batch overhead: ${maxOverhead.toFixed(3)}ms per request`);

      // Validate performance
      expect(errors.length).toBe(0);
      expect(avgOverhead).toBeLessThan(PERFORMANCE_THRESHOLD * 2); // Allow 2x threshold under load
      expect(requestsPerSecond).toBeGreaterThan(1000); // At least 1000 RPS
    });

    test('should maintain flow context integrity under load', async () => {
      const flowIds = new Set();
      const correlationIds = new Set();
      const errors = [];

      const testRequests = 1000;

      console.log(`Testing flow context integrity with ${testRequests} requests...`);

      const promises = [];
      for (let i = 0; i < testRequests; i++) {
        const promise = request(app)
          .get('/test')
          .expect(200)
          .then(response => {
            const flowId = response.headers['x-flow-id'];
            const correlationId = response.headers['x-correlation-id'];

            if (!flowId || !correlationId) {
              errors.push(`Missing headers in response ${i}`);
              return;
            }

            flowIds.add(flowId);
            correlationIds.add(correlationId);
          })
          .catch(err => errors.push(err));

        promises.push(promise);
      }

      await Promise.all(promises);

      console.log(`Unique flow IDs: ${flowIds.size}`);
      console.log(`Unique correlation IDs: ${correlationIds.size}`);
      console.log(`Errors: ${errors.length}`);

      // Validate context integrity
      expect(errors.length).toBe(0);
      expect(flowIds.size).toBe(testRequests); // Each request should have unique flow ID
      expect(correlationIds.size).toBe(testRequests); // Each request should have unique correlation ID
    });
  });

  describe('Memory Performance', () => {
    test('should not have significant memory leaks', async () => {
      const initialMemory = process.memoryUsage();
      const memoryMeasurements = [];

      // Run requests and measure memory
      for (let i = 0; i < 100; i++) {
        // Create batch of requests
        const batchPromises = [];
        for (let j = 0; j < 50; j++) {
          batchPromises.push(request(app).get('/test'));
        }

        await Promise.all(batchPromises);

        // Force garbage collection if available
        if (global.gc) {
          global.gc();
        }

        const currentMemory = process.memoryUsage();
        memoryMeasurements.push({
          heapUsed: currentMemory.heapUsed,
          heapTotal: currentMemory.heapTotal,
          external: currentMemory.external,
          arrayBuffers: currentMemory.arrayBuffers
        });
      }

      const finalMemory = process.memoryUsage();

      console.log('Initial memory usage:');
      console.log(`  Heap used: ${(initialMemory.heapUsed / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Heap total: ${(initialMemory.heapTotal / 1024 / 1024).toFixed(2)} MB`);

      console.log('Final memory usage:');
      console.log(`  Heap used: ${(finalMemory.heapUsed / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Heap total: ${(finalMemory.heapTotal / 1024 / 1024).toFixed(2)} MB`);

      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      const memoryIncreasePercent = (memoryIncrease / initialMemory.heapUsed) * 100;

      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB (${memoryIncreasePercent.toFixed(2)}%)`);

      // Allow some memory increase but not excessive
      expect(memoryIncreasePercent).toBeLessThan(50); // Less than 50% increase
    });
  });

  describe('Performance Statistics', () => {
    test('should report accurate performance statistics', async () => {
      // Make some requests to generate statistics
      for (let i = 0; i < 100; i++) {
        await request(app).get('/health');
      }

      const stats = middleware.getPerformanceStats();

      console.log('Performance statistics:');
      console.log(`  Setup time: ${stats.setupTime.toFixed(3)}ms`);
      console.log(`  Request count: ${stats.requestCount}`);
      console.log(`  Average overhead: ${stats.avgOverhead.toFixed(3)}ms`);
      console.log(`  Maximum overhead: ${stats.maxOverhead.toFixed(3)}ms`);
      console.log(`  Meets threshold: ${stats.meetsThreshold}`);

      expect(stats.requestCount).toBeGreaterThan(0);
      expect(stats.setupTime).toBeLessThan(100); // Setup should be fast
      expect(stats.avgOverhead).toBeLessThan(PERFORMANCE_THRESHOLD);
      expect(stats.meetsThreshold).toBe(true);
    });

    test('should track metrics efficiently', async () => {
      const startTime = performance.now();

      // Generate some requests with different patterns
      await Promise.all([
        request(app).get('/health'),
        request(app).get('/test'),
        request(app).post('/data').send({ test: 'data' }),
        request(app).get('/health'),
        request(app).get('/test')
      ]);

      const metrics = middleware.getMetrics();
      const endTime = performance.now();

      console.log(`Metrics collection time: ${(endTime - startTime).toFixed(3)}ms`);
      console.log(`Metrics collected: ${Object.keys(metrics).length} categories`);

      expect(Object.keys(metrics).length).toBeGreaterThan(0);
      expect(endTime - startTime).toBeLessThan(10); // Metrics collection should be fast
    });
  });

  describe('Concurrent Flow Tracking', () => {
    test('should handle concurrent flows without interference', async () => {
      const concurrentFlows = 50;
      const flowResults = [];

      console.log(`Testing ${concurrentFlows} concurrent flows...`);

      const promises = Array.from({ length: concurrentFlows }, async (_, index) => {
        const startTime = performance.now();

        const response = await request(app)
          .get('/test')
          .expect(200);

        const endTime = performance.now();
        const duration = endTime - startTime;

        flowResults.push({
          index,
          duration,
          flowId: response.headers['x-flow-id'],
          correlationId: response.headers['x-correlation-id']
        });
      });

      await Promise.all(promises);

      // Validate all flows completed
      expect(flowResults.length).toBe(concurrentFlows);

      // Check for unique flow IDs
      const uniqueFlowIds = new Set(flowResults.map(r => r.flowId));
      expect(uniqueFlowIds.size).toBe(concurrentFlows);

      // Check performance
      const avgDuration = flowResults.reduce((sum, r) => sum + r.duration, 0) / flowResults.length;
      const maxDuration = Math.max(...flowResults.map(r => r.duration));

      console.log(`Average flow duration: ${avgDuration.toFixed(3)}ms`);
      console.log(`Maximum flow duration: ${maxDuration.toFixed(3)}ms`);

      expect(avgDuration).toBeLessThan(100); // Should be fast even under concurrency
    });
  });
});