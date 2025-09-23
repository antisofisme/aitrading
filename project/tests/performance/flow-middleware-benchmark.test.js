/**
 * Flow Middleware Performance Benchmark Tests
 * Validates <1ms middleware overhead requirement
 */

const { expect } = require('chai');
const express = require('express');
const supertest = require('supertest');
const { performance } = require('perf_hooks');
const flowMiddleware = require('../../backend/configuration-service/src/middleware/flowMiddleware');

describe('Flow Middleware Performance Benchmarks', function() {
  this.timeout(60000);

  let app;
  let server;
  let baselineApp;
  let baselineServer;

  before(function() {
    // Create baseline app without middleware
    baselineApp = express();
    baselineApp.use(express.json());
    baselineApp.get('/baseline', (req, res) => {
      res.json({ message: 'baseline response', timestamp: Date.now() });
    });
    baselineServer = baselineApp.listen(0);

    // Create test app with flow middleware
    app = express();
    app.use(express.json());

    // Add flow middleware stack
    app.use(flowMiddleware.requestId);
    app.use(flowMiddleware.requestLogger);
    app.use(flowMiddleware.sanitizeInput);
    app.use(flowMiddleware.auditFlowExecution);
    app.use(flowMiddleware.flowCors);

    // Mock flow registry for middleware tests
    app.use((req, res, next) => {
      req.flowRegistry = {
        getFlow: async (id) => ({ id, name: 'Test Flow', type: 'test' }),
        trackExecution: async () => ({ id: 'exec-123' })
      };
      next();
    });

    app.get('/test', (req, res) => {
      res.json({ message: 'middleware response', timestamp: Date.now() });
    });

    app.post('/flows/:flowId/execute',
      flowMiddleware.auditFlowExecution,
      (req, res) => {
        res.json({
          executionId: 'test-exec-' + Date.now(),
          status: 'completed',
          result: { processed: true }
        });
      }
    );

    app.use(flowMiddleware.flowErrorHandler);

    server = app.listen(0);
  });

  after(function() {
    if (server) server.close();
    if (baselineServer) baselineServer.close();
  });

  describe('Middleware Overhead Measurement', function() {
    it('should measure baseline request performance', async function() {
      const iterations = 1000;
      const times = [];

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();

        await supertest(baselineApp)
          .get('/baseline')
          .expect(200);

        const end = performance.now();
        times.push(end - start);
      }

      const avgBaseline = times.reduce((a, b) => a + b) / times.length;
      const p95Baseline = times.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];

      console.log(`Baseline Average: ${avgBaseline.toFixed(3)}ms`);
      console.log(`Baseline P95: ${p95Baseline.toFixed(3)}ms`);

      // Store baseline for comparison
      this.baseline = { avg: avgBaseline, p95: p95Baseline };
    });

    it('should measure middleware request performance', async function() {
      const iterations = 1000;
      const times = [];

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();

        await supertest(app)
          .get('/test')
          .expect(200);

        const end = performance.now();
        times.push(end - start);
      }

      const avgMiddleware = times.reduce((a, b) => a + b) / times.length;
      const p95Middleware = times.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];

      console.log(`Middleware Average: ${avgMiddleware.toFixed(3)}ms`);
      console.log(`Middleware P95: ${p95Middleware.toFixed(3)}ms`);

      // Calculate overhead
      const avgOverhead = avgMiddleware - this.baseline.avg;
      const p95Overhead = p95Middleware - this.baseline.p95;

      console.log(`Average Overhead: ${avgOverhead.toFixed(3)}ms`);
      console.log(`P95 Overhead: ${p95Overhead.toFixed(3)}ms`);

      // Validate <1ms overhead requirement
      expect(avgOverhead).to.be.below(1.0,
        `Average middleware overhead (${avgOverhead.toFixed(3)}ms) should be less than 1ms`);
      expect(p95Overhead).to.be.below(2.0,
        `P95 middleware overhead (${p95Overhead.toFixed(3)}ms) should be less than 2ms`);
    });

    it('should measure audit middleware overhead specifically', async function() {
      const iterations = 500;
      const auditTimes = [];

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();

        await supertest(app)
          .post('/flows/test-flow-123/execute')
          .send({ parameters: { test: true } })
          .expect(200);

        const end = performance.now();
        auditTimes.push(end - start);
      }

      const avgAuditTime = auditTimes.reduce((a, b) => a + b) / auditTimes.length;
      const p95AuditTime = auditTimes.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];

      console.log(`Audit Middleware Average: ${avgAuditTime.toFixed(3)}ms`);
      console.log(`Audit Middleware P95: ${p95AuditTime.toFixed(3)}ms`);

      // Audit overhead should still be reasonable
      const auditOverhead = avgAuditTime - this.baseline.avg;
      console.log(`Audit Overhead: ${auditOverhead.toFixed(3)}ms`);

      expect(auditOverhead).to.be.below(2.0,
        `Audit middleware overhead should be reasonable`);
    });
  });

  describe('Concurrent Load Performance', function() {
    it('should handle concurrent requests efficiently', async function() {
      const concurrency = 50;
      const requestsPerWorker = 20;
      const promises = [];

      const start = performance.now();

      for (let i = 0; i < concurrency; i++) {
        const workerPromises = [];
        for (let j = 0; j < requestsPerWorker; j++) {
          workerPromises.push(
            supertest(app)
              .get('/test')
              .expect(200)
          );
        }
        promises.push(Promise.all(workerPromises));
      }

      await Promise.all(promises);
      const totalTime = performance.now() - start;

      const totalRequests = concurrency * requestsPerWorker;
      const avgTimePerRequest = totalTime / totalRequests;

      console.log(`Concurrent test: ${totalRequests} requests in ${totalTime.toFixed(2)}ms`);
      console.log(`Average time per request: ${avgTimePerRequest.toFixed(3)}ms`);

      expect(avgTimePerRequest).to.be.below(5.0,
        'Average time per concurrent request should be reasonable');
    });

    it('should maintain performance under sustained load', async function() {
      const duration = 10000; // 10 seconds
      const startTime = Date.now();
      const requests = [];
      let requestCount = 0;

      while (Date.now() - startTime < duration) {
        const batchPromises = [];

        // Send 10 requests in parallel
        for (let i = 0; i < 10; i++) {
          batchPromises.push(
            supertest(app)
              .get('/test')
              .expect(200)
              .then(() => requestCount++)
          );
        }

        requests.push(Promise.all(batchPromises));

        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      await Promise.all(requests);
      const actualDuration = Date.now() - startTime;
      const requestsPerSecond = (requestCount / actualDuration) * 1000;

      console.log(`Sustained load: ${requestCount} requests in ${actualDuration}ms`);
      console.log(`Requests per second: ${requestsPerSecond.toFixed(2)}`);

      expect(requestsPerSecond).to.be.above(100,
        'Should handle at least 100 requests per second');
    });
  });

  describe('Memory Usage Optimization', function() {
    it('should not leak memory during extended operations', async function() {
      const initialMemory = process.memoryUsage();
      const iterations = 1000;

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      for (let i = 0; i < iterations; i++) {
        await supertest(app)
          .post('/flows/memory-test-flow/execute')
          .send({
            parameters: {
              data: new Array(100).fill('test-data-' + i).join('')
            }
          })
          .expect(200);

        // Periodic cleanup
        if (i % 100 === 0 && global.gc) {
          global.gc();
        }
      }

      // Final cleanup
      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      const memoryIncreasePerRequest = memoryIncrease / iterations;

      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB`);
      console.log(`Memory per request: ${memoryIncreasePerRequest} bytes`);

      // Memory increase should be reasonable
      expect(memoryIncrease).to.be.below(50 * 1024 * 1024,
        'Memory increase should be less than 50MB');
      expect(memoryIncreasePerRequest).to.be.below(1024,
        'Memory per request should be less than 1KB');
    });

    it('should efficiently handle large request payloads', async function() {
      const largePayload = {
        parameters: {
          largeArray: new Array(10000).fill(0).map((_, i) => ({
            id: i,
            data: `large-data-item-${i}`,
            timestamp: Date.now(),
            metadata: { index: i, type: 'test' }
          }))
        }
      };

      const start = performance.now();

      const response = await supertest(app)
        .post('/flows/large-payload-test/execute')
        .send(largePayload)
        .expect(200);

      const processingTime = performance.now() - start;

      console.log(`Large payload processing time: ${processingTime.toFixed(3)}ms`);

      expect(response.body).to.have.property('executionId');
      expect(processingTime).to.be.below(1000,
        'Large payload processing should complete within 1 second');
    });
  });

  describe('Error Handling Performance', function() {
    it('should handle errors efficiently without performance degradation', async function() {
      const iterations = 200;
      const errorTimes = [];

      // Create an endpoint that always throws an error
      app.get('/error-test', (req, res, next) => {
        const error = new Error('Test error for performance measurement');
        error.status = 500;
        next(error);
      });

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();

        await supertest(app)
          .get('/error-test')
          .expect(500);

        const end = performance.now();
        errorTimes.push(end - start);
      }

      const avgErrorTime = errorTimes.reduce((a, b) => a + b) / errorTimes.length;
      console.log(`Average error handling time: ${avgErrorTime.toFixed(3)}ms`);

      expect(avgErrorTime).to.be.below(5.0,
        'Error handling should be fast');
    });

    it('should maintain performance during mixed success/error scenarios', async function() {
      const iterations = 100;
      const promises = [];

      const start = performance.now();

      for (let i = 0; i < iterations; i++) {
        if (i % 3 === 0) {
          // Error request
          promises.push(
            supertest(app)
              .get('/error-test')
              .expect(500)
          );
        } else {
          // Success request
          promises.push(
            supertest(app)
              .get('/test')
              .expect(200)
          );
        }
      }

      await Promise.all(promises);
      const totalTime = performance.now() - start;
      const avgTime = totalTime / iterations;

      console.log(`Mixed scenario average time: ${avgTime.toFixed(3)}ms`);

      expect(avgTime).to.be.below(10.0,
        'Mixed success/error scenario should maintain good performance');
    });
  });

  describe('Resource Usage Monitoring', function() {
    it('should track CPU usage during high load', async function() {
      const start = process.cpuUsage();
      const wallStart = performance.now();

      // Generate sustained load
      const promises = [];
      for (let i = 0; i < 500; i++) {
        promises.push(
          supertest(app)
            .post('/flows/cpu-test/execute')
            .send({ parameters: { iteration: i } })
            .expect(200)
        );
      }

      await Promise.all(promises);

      const cpuUsage = process.cpuUsage(start);
      const wallTime = performance.now() - wallStart;

      const cpuPercent = ((cpuUsage.user + cpuUsage.system) / 1000) / wallTime * 100;

      console.log(`CPU usage during load test: ${cpuPercent.toFixed(2)}%`);
      console.log(`Wall time: ${wallTime.toFixed(2)}ms`);

      expect(cpuPercent).to.be.below(80,
        'CPU usage should be reasonable during high load');
    });

    it('should validate middleware initialization overhead', async function() {
      // Test middleware setup time
      const setupStart = performance.now();

      const testApp = express();
      testApp.use(express.json());
      testApp.use(flowMiddleware.requestId);
      testApp.use(flowMiddleware.requestLogger);
      testApp.use(flowMiddleware.sanitizeInput);
      testApp.use(flowMiddleware.auditFlowExecution);
      testApp.use(flowMiddleware.flowCors);
      testApp.use(flowMiddleware.flowErrorHandler);

      const setupTime = performance.now() - setupStart;

      console.log(`Middleware setup time: ${setupTime.toFixed(3)}ms`);

      expect(setupTime).to.be.below(10,
        'Middleware setup should be fast');
    });
  });
});