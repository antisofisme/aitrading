/**
 * Integration Tests for Cross-Service Flow Tracking
 * Tests end-to-end flow tracking across multiple services and error propagation
 */

const request = require('supertest');
const FlowRegistry = require('@mocks/flow-registry');
const ChainHealthMonitor = require('@mocks/chain-health-monitor');
const ChainImpactAnalyzer = require('@mocks/chain-impact-analyzer');
const {
  createTestServices,
  generateFlowId,
  simulateServiceError,
  waitForPropagation
} = require('@utils/integration-helpers');

describe('Cross-Service Flow Tracking Integration Tests', () => {
  let testServices;
  let flowRegistry;
  let healthMonitor;
  let impactAnalyzer;
  let mockLogger;

  beforeAll(async () => {
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    // Initialize components
    flowRegistry = new FlowRegistry({ logger: mockLogger });
    healthMonitor = new ChainHealthMonitor({ logger: mockLogger });
    impactAnalyzer = new ChainImpactAnalyzer({
      logger: mockLogger,
      flowRegistry,
      healthMonitor
    });

    // Create test service instances
    testServices = await createTestServices([
      {
        name: 'api-gateway',
        port: 3001,
        dependencies: [],
        routes: ['/api/trade', '/api/user']
      },
      {
        name: 'auth-service',
        port: 3002,
        dependencies: ['database'],
        routes: ['/auth/validate', '/auth/refresh']
      },
      {
        name: 'trading-engine',
        port: 3003,
        dependencies: ['auth-service', 'market-data', 'risk-engine'],
        routes: ['/trade/execute', '/trade/validate']
      },
      {
        name: 'market-data',
        port: 3004,
        dependencies: ['external-feed'],
        routes: ['/market/price', '/market/volume']
      },
      {
        name: 'risk-engine',
        port: 3005,
        dependencies: ['database', 'market-data'],
        routes: ['/risk/assess', '/risk/limits']
      },
      {
        name: 'database',
        port: 3006,
        dependencies: [],
        routes: ['/health', '/status']
      }
    ]);

    // Register services with health monitor
    for (const service of testServices) {
      await healthMonitor.registerService(service.name, {
        name: service.name,
        healthEndpoint: `http://localhost:${service.port}/health`,
        dependencies: service.dependencies
      });
    }

    await healthMonitor.startMonitoring();
  });

  afterAll(async () => {
    await healthMonitor.stopMonitoring();
    for (const service of testServices) {
      await service.stop();
    }
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('End-to-End Flow Tracking', () => {
    it('should track a complete trade execution flow across services', async () => {
      const flowId = generateFlowId();
      const tradeRequest = {
        symbol: 'BTCUSD',
        quantity: 1.5,
        orderType: 'market',
        userId: 'user123'
      };

      // Start flow at API Gateway
      const gatewayResponse = await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({ ...tradeRequest, flowId })
        .expect(200);

      expect(gatewayResponse.body.flowId).toBe(flowId);

      // Wait for flow propagation across services
      await waitForPropagation(2000);

      // Verify flow was tracked through each service
      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.success).toBe(true);
      expect(flow.flow.steps).toHaveLength(6); // One step per service

      const serviceSteps = flow.flow.steps.map(step => step.serviceId);
      expect(serviceSteps).toContain('api-gateway');
      expect(serviceSteps).toContain('auth-service');
      expect(serviceSteps).toContain('trading-engine');
      expect(serviceSteps).toContain('market-data');
      expect(serviceSteps).toContain('risk-engine');
      expect(serviceSteps).toContain('database');

      // Verify flow completion
      expect(flow.flow.status).toBe('completed');
      expect(flow.flow.duration).toBeGreaterThan(0);
    });

    it('should track parallel service calls within a flow', async () => {
      const flowId = generateFlowId();
      const complexTradeRequest = {
        symbol: 'ETHUSD',
        quantity: 10,
        orderType: 'limit',
        price: 2500,
        userId: 'user456'
      };

      // Initiate complex trade that requires parallel calls
      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade/complex')
        .send({ ...complexTradeRequest, flowId })
        .expect(200);

      await waitForPropagation(3000);

      const flow = await flowRegistry.getFlow(flowId);

      // Should have parallel steps for market-data and risk-engine
      const parallelSteps = flow.flow.steps.filter(step =>
        step.parallel && (step.serviceId === 'market-data' || step.serviceId === 'risk-engine')
      );
      expect(parallelSteps).toHaveLength(2);

      // Verify timing - parallel steps should have similar timestamps
      const timeDifference = Math.abs(parallelSteps[0].timestamp - parallelSteps[1].timestamp);
      expect(timeDifference).toBeLessThan(100); // Within 100ms
    });

    it('should maintain flow context across service boundaries', async () => {
      const flowId = generateFlowId();
      const userContext = {
        userId: 'user789',
        sessionId: 'sess_abc123',
        permissions: ['trade', 'view_portfolio'],
        riskProfile: 'moderate'
      };

      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({
          flowId,
          symbol: 'ADAUSD',
          quantity: 1000,
          context: userContext
        })
        .expect(200);

      await waitForPropagation(2000);

      const flow = await flowRegistry.getFlow(flowId);

      // Verify context was preserved in each step
      flow.flow.steps.forEach(step => {
        expect(step.context.userId).toBe('user789');
        expect(step.context.sessionId).toBe('sess_abc123');
      });

      // Verify context enrichment in specific services
      const riskStep = flow.flow.steps.find(s => s.serviceId === 'risk-engine');
      expect(riskStep.context.riskAssessment).toBeDefined();

      const authStep = flow.flow.steps.find(s => s.serviceId === 'auth-service');
      expect(authStep.context.authValidated).toBe(true);
    });
  });

  describe('Error Propagation and Impact Analysis', () => {
    it('should track error propagation through service chain', async () => {
      const flowId = generateFlowId();

      // Simulate database failure
      await simulateServiceError(testServices.find(s => s.name === 'database'), {
        type: 'connection_timeout',
        duration: 5000
      });

      // Attempt trade execution
      const response = await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({
          flowId,
          symbol: 'BTCUSD',
          quantity: 0.5,
          userId: 'user999'
        })
        .expect(500);

      await waitForPropagation(2000);

      // Analyze error propagation
      const impactAnalysis = await impactAnalyzer.analyzeError(response.body.errorId, response.body.error);

      expect(impactAnalysis.success).toBe(true);
      expect(impactAnalysis.impact.cascadingServices).toContain('auth-service');
      expect(impactAnalysis.impact.cascadingServices).toContain('risk-engine');
      expect(impactAnalysis.rootCause.serviceId).toBe('database');

      // Verify flow recorded the error
      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.flow.status).toBe('error');
      expect(flow.flow.errors).toHaveLength(1);
    });

    it('should handle circuit breaker activation across services', async () => {
      const flowIds = [];

      // Simulate sustained database issues to trigger circuit breaker
      await simulateServiceError(testServices.find(s => s.name === 'database'), {
        type: 'sustained_failure',
        duration: 10000,
        errorRate: 1.0
      });

      // Generate multiple requests to trigger circuit breaker
      for (let i = 0; i < 10; i++) {
        const flowId = generateFlowId();
        flowIds.push(flowId);

        await request(testServices.find(s => s.name === 'api-gateway').app)
          .post('/api/trade')
          .send({
            flowId,
            symbol: 'ETHUSD',
            quantity: 1,
            userId: `user${i}`
          });
      }

      await waitForPropagation(3000);

      // Verify circuit breaker was activated
      const healthStatus = await healthMonitor.getServiceHealth('database');
      expect(healthStatus.circuitBreakerState).toBe('open');

      // Verify subsequent requests fail fast
      const fastFailFlowId = generateFlowId();
      const startTime = Date.now();

      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({
          flowId: fastFailFlowId,
          symbol: 'ADAUSD',
          quantity: 100,
          userId: 'fast_fail_user'
        })
        .expect(503);

      const responseTime = Date.now() - startTime;
      expect(responseTime).toBeLessThan(100); // Should fail fast
    });

    it('should analyze cross-service transaction rollback', async () => {
      const flowId = generateFlowId();

      // Configure trading engine to fail after risk assessment
      await simulateServiceError(testServices.find(s => s.name === 'trading-engine'), {
        type: 'execution_failure',
        stage: 'after_risk_assessment'
      });

      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade/atomic')
        .send({
          flowId,
          symbol: 'SOLUSD',
          quantity: 50,
          userId: 'rollback_user'
        })
        .expect(500);

      await waitForPropagation(3000);

      const flow = await flowRegistry.getFlow(flowId);

      // Verify rollback was tracked
      const rollbackSteps = flow.flow.steps.filter(step => step.action === 'rollback');
      expect(rollbackSteps).toHaveLength(2); // Risk engine and auth service

      // Verify rollback order (reverse of execution order)
      expect(rollbackSteps[0].serviceId).toBe('risk-engine');
      expect(rollbackSteps[1].serviceId).toBe('auth-service');
    });
  });

  describe('Performance and Scalability Under Load', () => {
    it('should track flows under high concurrent load', async () => {
      const concurrentFlows = 100;
      const flowIds = [];
      const promises = [];

      // Generate concurrent requests
      for (let i = 0; i < concurrentFlows; i++) {
        const flowId = generateFlowId();
        flowIds.push(flowId);

        promises.push(
          request(testServices.find(s => s.name === 'api-gateway').app)
            .post('/api/trade')
            .send({
              flowId,
              symbol: 'BTCUSD',
              quantity: 0.1,
              userId: `concurrent_user_${i}`
            })
        );
      }

      const startTime = Date.now();
      const responses = await Promise.all(promises);
      const totalTime = Date.now() - startTime;

      // Verify all requests completed
      expect(responses.length).toBe(concurrentFlows);

      // Verify reasonable performance (less than 10 seconds for 100 requests)
      expect(totalTime).toBeLessThan(10000);

      await waitForPropagation(5000);

      // Verify all flows were tracked
      let successfulFlows = 0;
      for (const flowId of flowIds) {
        const flow = await flowRegistry.getFlow(flowId);
        if (flow.success && flow.flow.status === 'completed') {
          successfulFlows++;
        }
      }

      // At least 95% success rate under load
      expect(successfulFlows / concurrentFlows).toBeGreaterThan(0.95);
    });

    it('should maintain tracking accuracy under memory pressure', async () => {
      const largeDataFlows = 50;
      const flowIds = [];

      // Generate flows with large context data
      for (let i = 0; i < largeDataFlows; i++) {
        const flowId = generateFlowId();
        flowIds.push(flowId);

        const largeContext = {
          userId: `memory_test_user_${i}`,
          sessionData: 'x'.repeat(10000), // 10KB per flow
          historicalData: new Array(1000).fill().map((_, j) => ({
            timestamp: Date.now() - j * 1000,
            value: Math.random() * 1000
          }))
        };

        await request(testServices.find(s => s.name === 'api-gateway').app)
          .post('/api/trade')
          .send({
            flowId,
            symbol: 'ETHUSD',
            quantity: 1,
            context: largeContext
          });
      }

      await waitForPropagation(10000);

      // Verify all flows are still tracked correctly
      for (const flowId of flowIds) {
        const flow = await flowRegistry.getFlow(flowId);
        expect(flow.success).toBe(true);
        expect(flow.flow.steps.length).toBeGreaterThan(0);
      }

      // Verify system didn't run out of memory
      const memoryUsage = process.memoryUsage();
      expect(memoryUsage.heapUsed).toBeLessThan(500 * 1024 * 1024); // Less than 500MB
    });
  });

  describe('Service Health Integration', () => {
    it('should correlate flow failures with service health', async () => {
      const flowId = generateFlowId();

      // Simulate gradual service degradation
      await simulateServiceError(testServices.find(s => s.name === 'market-data'), {
        type: 'gradual_degradation',
        duration: 5000,
        degradationRate: 0.2 // 20% per second
      });

      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({
          flowId,
          symbol: 'DOTUSD',
          quantity: 25,
          userId: 'health_correlation_user'
        });

      await waitForPropagation(6000);

      const flow = await flowRegistry.getFlow(flowId);
      const healthAnalysis = await impactAnalyzer.correlateWithHealth(flowId);

      expect(healthAnalysis.correlatedServices).toContain('market-data');
      expect(healthAnalysis.healthScore).toBeLessThan(0.8); // Degraded health
      expect(flow.flow.metadata.healthCorrelation).toBeDefined();
    });

    it('should predict flow success based on service health', async () => {
      // Set varying health states
      await healthMonitor._setServiceHealth('api-gateway', 'healthy', 0.99);
      await healthMonitor._setServiceHealth('auth-service', 'degraded', 0.85);
      await healthMonitor._setServiceHealth('trading-engine', 'healthy', 0.97);
      await healthMonitor._setServiceHealth('market-data', 'unhealthy', 0.60);
      await healthMonitor._setServiceHealth('risk-engine', 'healthy', 0.95);
      await healthMonitor._setServiceHealth('database', 'healthy', 0.98);

      const flowId = generateFlowId();
      const prediction = await impactAnalyzer.predictFlowSuccess(flowId, {
        services: ['api-gateway', 'auth-service', 'trading-engine', 'market-data', 'risk-engine', 'database']
      });

      expect(prediction.successProbability).toBeLessThan(0.7); // Low due to market-data health
      expect(prediction.riskFactors).toContain('market-data');
      expect(prediction.recommendation).toContain('delay');
    });
  });

  describe('Real-time Monitoring and Alerting', () => {
    it('should trigger real-time alerts on flow anomalies', async () => {
      const mockAlertHandler = jest.fn();
      impactAnalyzer.on('flowAnomaly', mockAlertHandler);

      const flowId = generateFlowId();

      // Simulate unusually long processing time
      await simulateServiceError(testServices.find(s => s.name === 'risk-engine'), {
        type: 'processing_delay',
        delay: 10000 // 10 second delay
      });

      await request(testServices.find(s => s.name === 'api-gateway').app)
        .post('/api/trade')
        .send({
          flowId,
          symbol: 'AVAXUSD',
          quantity: 5,
          userId: 'anomaly_user'
        });

      await waitForPropagation(12000);

      expect(mockAlertHandler).toHaveBeenCalledWith({
        type: 'unusual_processing_time',
        flowId,
        affectedService: 'risk-engine',
        actualTime: expect.any(Number),
        expectedTime: expect.any(Number),
        severity: 'medium'
      });
    });

    it('should aggregate flow metrics for dashboards', async () => {
      // Generate diverse flow patterns
      const flowTypes = [
        { symbol: 'BTCUSD', quantity: 1, expected: 'fast' },
        { symbol: 'ETHUSD', quantity: 10, expected: 'medium' },
        { symbol: 'ADAUSD', quantity: 1000, expected: 'slow' }
      ];

      const flowIds = [];
      for (let i = 0; i < 30; i++) {
        const flowId = generateFlowId();
        flowIds.push(flowId);
        const flowType = flowTypes[i % 3];

        await request(testServices.find(s => s.name === 'api-gateway').app)
          .post('/api/trade')
          .send({
            flowId,
            symbol: flowType.symbol,
            quantity: flowType.quantity,
            userId: `metrics_user_${i}`
          });
      }

      await waitForPropagation(5000);

      const metrics = await flowRegistry.getAggregateMetrics({
        timeWindow: 300000, // 5 minutes
        groupBy: ['symbol', 'status']
      });

      expect(metrics.totalFlows).toBe(30);
      expect(metrics.bySymbol.BTCUSD).toBe(10);
      expect(metrics.bySymbol.ETHUSD).toBe(10);
      expect(metrics.bySymbol.ADAUSD).toBe(10);
      expect(metrics.averageProcessingTime).toBeGreaterThan(0);
    });
  });
});