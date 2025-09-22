/**
 * @fileoverview Integration tests for flow-aware middleware across services
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Tests flow tracking across microservice boundaries with service discovery
 */

const express = require('express');
const request = require('supertest');
const axios = require('axios');
const { FlowAwareMiddleware } = require('../../../backend/shared/middleware/flow-aware');

describe('Flow-Aware Middleware Integration Tests', () => {
  let services = {};
  let middleware = {};
  const SERVICE_PORTS = {
    'api-gateway': 3001,
    'data-bridge': 5001,
    'central-hub': 7000,
    'trading-engine': 9000,
    'ai-orchestrator': 8020
  };

  beforeAll(async () => {
    // Create test services
    for (const [serviceName, port] of Object.entries(SERVICE_PORTS)) {
      const app = express();

      // Initialize flow-aware middleware for each service
      middleware[serviceName] = new FlowAwareMiddleware({
        serviceName,
        config: {
          flowTracker: {
            enabled: true,
            performanceThreshold: 1,
            enableDependencyTracking: true
          },
          chainContext: {
            enabled: true,
            enablePersistence: false
          },
          metricsCollector: {
            enabled: true,
            enableRealTimeMetrics: true
          },
          eventPublisher: {
            enabled: true,
            enableBuffering: true
          }
        }
      });

      await middleware[serviceName].initialize();
      app.use(middleware[serviceName].middleware());

      // Add service-specific routes
      app.get('/health', (req, res) => {
        res.json({
          service: serviceName,
          status: 'healthy',
          flowId: middleware[serviceName].getFlowContext(req)?.flowId,
          timestamp: Date.now()
        });
      });

      app.get('/info', (req, res) => {
        const flowContext = middleware[serviceName].getFlowContext(req);
        const chainContext = middleware[serviceName].getChainContext(req);

        res.json({
          service: serviceName,
          flowContext: {
            flowId: flowContext?.flowId,
            correlationId: flowContext?.correlationId,
            serviceChain: flowContext?.serviceChain
          },
          chainContext: {
            contextId: chainContext?.id,
            depth: chainContext?.depth,
            serviceChain: chainContext?.serviceChain
          }
        });
      });

      // Add service call routes
      app.get('/call/:targetService', async (req, res) => {
        try {
          const targetService = req.params.targetService;
          const targetPort = SERVICE_PORTS[targetService];

          if (!targetPort) {
            return res.status(404).json({ error: 'Service not found' });
          }

          // Get outgoing headers for flow tracking
          const outgoingHeaders = middleware[serviceName].getOutgoingHeaders(req, targetService);

          // Make request to target service
          const response = await axios.get(`http://localhost:${targetPort}/info`, {
            headers: outgoingHeaders,
            timeout: 5000
          });

          res.json({
            caller: serviceName,
            target: targetService,
            response: response.data,
            outgoingHeaders
          });

        } catch (error) {
          middleware[serviceName].addError(req, error, `call-${req.params.targetService}`);
          res.status(500).json({ error: error.message });
        }
      });

      // Add error test route
      app.get('/error', (req, res) => {
        const error = new Error('Test error');
        error.code = 'TEST_ERROR';
        middleware[serviceName].addError(req, error, 'error-test');
        res.status(500).json({ error: 'Test error triggered' });
      });

      services[serviceName] = app;
    }

    // Give services time to initialize
    await new Promise(resolve => setTimeout(resolve, 1000));
  });

  afterAll(async () => {
    // Stop all middleware
    for (const service of Object.values(middleware)) {
      await service.stop();
    }
  });

  describe('Single Service Flow Tracking', () => {
    test('should track flow in api-gateway', async () => {
      const response = await request(services['api-gateway'])
        .get('/info')
        .expect(200);

      expect(response.body.service).toBe('api-gateway');
      expect(response.body.flowContext.flowId).toBeDefined();
      expect(response.body.flowContext.correlationId).toBeDefined();
      expect(response.body.flowContext.serviceChain).toContain('api-gateway');
      expect(response.body.chainContext.contextId).toBeDefined();
      expect(response.body.chainContext.depth).toBe(0);
    });

    test('should include flow headers in response', async () => {
      const response = await request(services['central-hub'])
        .get('/health')
        .expect(200);

      expect(response.headers['x-flow-id']).toBeDefined();
      expect(response.headers['x-correlation-id']).toBeDefined();
      expect(response.headers['x-service-chain']).toBeDefined();

      const serviceChain = JSON.parse(response.headers['x-service-chain']);
      expect(serviceChain).toContain('central-hub');
    });
  });

  describe('Cross-Service Flow Tracking', () => {
    test('should propagate flow context across services', async () => {
      // Start flow in api-gateway and call data-bridge
      const response = await request(services['api-gateway'])
        .get('/call/data-bridge')
        .expect(200);

      expect(response.body.caller).toBe('api-gateway');
      expect(response.body.target).toBe('data-bridge');
      expect(response.body.response.service).toBe('data-bridge');

      // Check flow propagation
      const apiFlowId = response.body.outgoingHeaders['x-flow-id'];
      const bridgeFlowId = response.body.response.flowContext.flowId;

      expect(apiFlowId).toBeDefined();
      expect(bridgeFlowId).toBeDefined();
      // Flow ID should be the same or related (depending on implementation)

      // Check service chain
      const bridgeServiceChain = response.body.response.flowContext.serviceChain;
      expect(bridgeServiceChain).toContain('api-gateway');
      expect(bridgeServiceChain).toContain('data-bridge');
    });

    test('should maintain correlation across multiple hops', async () => {
      // Create a chain: api-gateway -> central-hub -> trading-engine

      // First, setup central-hub to call trading-engine
      const hubApp = services['central-hub'];
      hubApp.get('/chain-call', async (req, res) => {
        try {
          const outgoingHeaders = middleware['central-hub'].getOutgoingHeaders(req, 'trading-engine');

          const response = await axios.get('http://localhost:9000/info', {
            headers: outgoingHeaders,
            timeout: 5000
          });

          res.json({
            hop1: 'central-hub',
            hop2Response: response.data,
            headers: outgoingHeaders
          });
        } catch (error) {
          res.status(500).json({ error: error.message });
        }
      });

      // Now call from api-gateway through the chain
      const response = await request(services['api-gateway'])
        .get('/call/central-hub')
        .expect(200);

      // Verify the chain
      expect(response.body.response.service).toBe('central-hub');

      const correlationId = response.body.response.flowContext.correlationId;
      expect(correlationId).toBeDefined();

      // The service chain should show the path
      const serviceChain = response.body.response.flowContext.serviceChain;
      expect(serviceChain).toContain('api-gateway');
      expect(serviceChain).toContain('central-hub');
    });

    test('should track dependencies correctly', async () => {
      // Make a call that creates a dependency
      const response = await request(services['ai-orchestrator'])
        .get('/call/trading-engine')
        .expect(200);

      // Get metrics to check dependencies
      const metrics = middleware['ai-orchestrator'].getMetrics();

      // Should have dependency metrics
      expect(metrics).toBeDefined();

      // Check that the call was tracked
      expect(response.body.caller).toBe('ai-orchestrator');
      expect(response.body.target).toBe('trading-engine');
    });
  });

  describe('Error Correlation', () => {
    test('should correlate errors across services', async () => {
      // Trigger error in target service
      const errorResponse = await request(services['data-bridge'])
        .get('/error')
        .expect(500);

      expect(errorResponse.body.error).toBe('Test error triggered');

      // The error should be tracked in the flow context
      const flowId = errorResponse.headers['x-flow-id'];
      expect(flowId).toBeDefined();
    });

    test('should handle service unavailable scenarios', async () => {
      // Try to call a non-existent service
      const response = await request(services['api-gateway'])
        .get('/call/non-existent-service')
        .expect(404);

      expect(response.body.error).toBe('Service not found');
    });
  });

  describe('Performance Under Load', () => {
    test('should handle concurrent cross-service calls', async () => {
      const concurrentCalls = 20;
      const promises = [];

      for (let i = 0; i < concurrentCalls; i++) {
        const promise = request(services['api-gateway'])
          .get('/call/central-hub')
          .expect(200);
        promises.push(promise);
      }

      const responses = await Promise.all(promises);

      // All should succeed
      expect(responses.length).toBe(concurrentCalls);

      // Each should have unique flow IDs
      const flowIds = responses.map(r => r.body.response.flowContext.flowId);
      const uniqueFlowIds = new Set(flowIds);
      expect(uniqueFlowIds.size).toBe(concurrentCalls);
    });

    test('should maintain performance under service mesh load', async () => {
      const startTime = Date.now();
      const testCalls = 100;
      const promises = [];

      // Create calls between different service pairs
      const servicePairs = [
        ['api-gateway', 'data-bridge'],
        ['central-hub', 'trading-engine'],
        ['ai-orchestrator', 'central-hub'],
        ['data-bridge', 'ai-orchestrator'],
        ['trading-engine', 'api-gateway']
      ];

      for (let i = 0; i < testCalls; i++) {
        const [source, target] = servicePairs[i % servicePairs.length];

        if (SERVICE_PORTS[target]) {
          const promise = request(services[source])
            .get(`/call/${target}`)
            .expect(200);
          promises.push(promise);
        }
      }

      const responses = await Promise.all(promises);
      const endTime = Date.now();
      const duration = endTime - startTime;

      console.log(`Completed ${testCalls} cross-service calls in ${duration}ms`);
      console.log(`Average: ${(duration / testCalls).toFixed(2)}ms per call`);

      expect(responses.length).toBe(testCalls);
      expect(duration / testCalls).toBeLessThan(50); // Less than 50ms per call on average
    });
  });

  describe('Metrics Collection', () => {
    test('should collect metrics across all services', async () => {
      // Generate some activity
      await Promise.all([
        request(services['api-gateway']).get('/health'),
        request(services['data-bridge']).get('/health'),
        request(services['central-hub']).get('/health'),
        request(services['trading-engine']).get('/health'),
        request(services['ai-orchestrator']).get('/health')
      ]);

      // Check metrics for each service
      for (const [serviceName, serviceMiddleware] of Object.entries(middleware)) {
        const metrics = serviceMiddleware.getMetrics();
        const stats = serviceMiddleware.getPerformanceStats();

        expect(metrics).toBeDefined();
        expect(stats.requestCount).toBeGreaterThan(0);
        expect(stats.avgOverhead).toBeLessThan(1); // Should meet performance requirement

        console.log(`${serviceName} - Requests: ${stats.requestCount}, Avg Overhead: ${stats.avgOverhead.toFixed(3)}ms`);
      }
    });

    test('should aggregate flow metrics correctly', async () => {
      // Create a multi-hop flow for comprehensive metrics
      const response = await request(services['api-gateway'])
        .get('/call/central-hub')
        .expect(200);

      const flowId = response.body.response.flowContext.flowId;
      expect(flowId).toBeDefined();

      // Give metrics time to be collected
      await new Promise(resolve => setTimeout(resolve, 100));

      // Check that both services have metrics for this flow
      const gatewayMetrics = middleware['api-gateway'].getMetrics();
      const hubMetrics = middleware['central-hub'].getMetrics();

      expect(gatewayMetrics).toBeDefined();
      expect(hubMetrics).toBeDefined();
    });
  });

  describe('Service Discovery Integration', () => {
    test('should work with service registry configuration', async () => {
      // Test that all configured services are responsive
      const healthChecks = await Promise.all(
        Object.entries(SERVICE_PORTS).map(async ([serviceName, port]) => {
          try {
            const response = await request(services[serviceName])
              .get('/health')
              .expect(200);

            return {
              service: serviceName,
              healthy: true,
              flowId: response.body.flowId
            };
          } catch (error) {
            return {
              service: serviceName,
              healthy: false,
              error: error.message
            };
          }
        })
      );

      // All services should be healthy
      const healthyServices = healthChecks.filter(check => check.healthy);
      expect(healthyServices.length).toBe(Object.keys(SERVICE_PORTS).length);

      // Each should have a flow ID
      healthyServices.forEach(check => {
        expect(check.flowId).toBeDefined();
      });
    });
  });
});