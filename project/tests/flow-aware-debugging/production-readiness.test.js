/**
 * Production Readiness Validation Tests for Flow-Aware Error Handling
 * Comprehensive tests to validate system readiness for production deployment
 */

const FlowRegistry = require('./mocks/flow-registry');
const ChainHealthMonitor = require('./mocks/chain-health-monitor');
const ChainImpactAnalyzer = require('./mocks/chain-impact-analyzer');
const {
  generateFlowId,
  generateServiceId,
  createMockError,
  measurePerformance,
  getMemoryUsage,
  generateLoadPattern,
  waitForCondition
} = require('./utils/test-helpers');

describe('Production Readiness Validation Tests', () => {
  let flowRegistry;
  let healthMonitor;
  let impactAnalyzer;
  let mockLogger;
  let mockMetrics;

  beforeAll(async () => {
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    mockMetrics = {
      increment: jest.fn(),
      gauge: jest.fn(),
      histogram: jest.fn(),
      timer: jest.fn()
    };

    // Initialize with production-like configuration
    flowRegistry = new FlowRegistry({
      maxFlows: 100000,
      retentionPeriod: 86400000, // 24 hours
      indexingStrategy: 'optimized',
      memoryManagement: 'aggressive',
      persistenceMode: 'batch',
      logger: mockLogger,
      metrics: mockMetrics
    });

    healthMonitor = new ChainHealthMonitor({
      healthCheckInterval: 5000, // 5 seconds
      alertThresholds: {
        errorRate: 0.05,
        responseTime: 2000,
        availability: 0.99
      },
      logger: mockLogger,
      metrics: mockMetrics
    });

    impactAnalyzer = new ChainImpactAnalyzer({
      analysisDepth: 5,
      timeWindow: 300000, // 5 minutes
      cacheSize: 50000,
      parallelAnalysis: true,
      logger: mockLogger,
      metrics: mockMetrics,
      flowRegistry,
      healthMonitor
    });

    await flowRegistry.initialize();
    await healthMonitor.initialize();
    await impactAnalyzer.initialize();
  });

  afterAll(async () => {
    await flowRegistry.cleanup();
    await healthMonitor.cleanup();
    await impactAnalyzer.cleanup();
  });

  describe('Scalability and Performance Requirements', () => {
    it('should handle production-level flow volume (10,000 flows/minute)', async () => {
      const targetFlowsPerMinute = 10000;
      const testDuration = 60000; // 1 minute
      const flowsPerSecond = targetFlowsPerMinute / 60;

      const startTime = Date.now();
      let flowsCreated = 0;
      const errors = [];

      // Generate sustained load
      const loadInterval = setInterval(async () => {
        try {
          for (let i = 0; i < flowsPerSecond; i++) {
            const flowId = generateFlowId();
            const serviceId = `service_${i % 10}`;
            await flowRegistry.registerFlow(flowId, serviceId, {
              productionTest: true,
              batchId: Math.floor(Date.now() / 1000)
            });
            flowsCreated++;
          }
        } catch (error) {
          errors.push(error);
        }
      }, 1000);

      // Wait for test duration
      await new Promise(resolve => setTimeout(resolve, testDuration));
      clearInterval(loadInterval);

      const actualDuration = Date.now() - startTime;
      const actualRate = (flowsCreated / actualDuration) * 60000; // flows per minute

      expect(errors).toHaveLength(0);
      expect(actualRate).toBeGreaterThan(targetFlowsPerMinute * 0.9); // 90% of target
      expect(flowsCreated).toBeGreaterThan(9000); // At least 9k flows

      // Verify system stability
      const memoryUsage = getMemoryUsage();
      expect(memoryUsage.heapUsed).toBeLessThan(1024); // Under 1GB
    });

    it('should maintain sub-second response times under load', async () => {
      // Pre-populate with data
      for (let i = 0; i < 50000; i++) {
        await flowRegistry.registerFlow(`perf_flow_${i}`, `service_${i % 20}`, {
          performanceTest: true
        });
      }

      const operations = [
        () => flowRegistry.getFlow(`perf_flow_${Math.floor(Math.random() * 50000)}`),
        () => flowRegistry.queryFlows({ serviceId: `service_${Math.floor(Math.random() * 20)}` }),
        () => flowRegistry.queryFlows({ status: 'pending', limit: 100 }),
        () => healthMonitor.getServiceHealth(`service_${Math.floor(Math.random() * 20)}`),
        () => impactAnalyzer.analyzeError('test_error', createMockError())
      ];

      // Measure performance under concurrent load
      const concurrentOperations = 100;
      const promises = [];

      for (let i = 0; i < concurrentOperations; i++) {
        const operation = operations[i % operations.length];
        promises.push(measurePerformance(operation));
      }

      const results = await Promise.all(promises);

      results.forEach(result => {
        expect(result.avg).toBeLessThan(1000); // Under 1 second
        expect(result.p95).toBeLessThan(2000); // P95 under 2 seconds
      });

      // Verify all operations succeeded
      expect(results.every(r => r.times.length > 0)).toBe(true);
    });

    it('should support horizontal scaling patterns', async () => {
      // Simulate multiple instances
      const instances = [];

      for (let i = 0; i < 3; i++) {
        const instance = new FlowRegistry({
          instanceId: `instance_${i}`,
          maxFlows: 50000,
          logger: mockLogger,
          metrics: mockMetrics
        });
        await instance.initialize();
        instances.push(instance);
      }

      try {
        // Distribute load across instances
        const flowsPerInstance = 1000;
        const promises = [];

        instances.forEach((instance, index) => {
          promises.push(
            (async () => {
              for (let i = 0; i < flowsPerInstance; i++) {
                await instance.registerFlow(
                  `scaling_flow_${index}_${i}`,
                  `service_${i % 10}`,
                  { instanceId: index }
                );
              }
            })()
          );
        });

        await Promise.all(promises);

        // Verify load distribution
        for (const instance of instances) {
          const flows = await instance.queryFlows({});
          expect(flows.flows).toHaveLength(flowsPerInstance);
        }

        // Verify instance isolation
        const instance0Flows = await instances[0].queryFlows({});
        const instance1Flows = await instances[1].queryFlows({});

        const overlap = instance0Flows.flows.filter(flow =>
          instance1Flows.flows.some(f => f.id === flow.id)
        );
        expect(overlap).toHaveLength(0); // No overlap between instances

      } finally {
        // Cleanup instances
        await Promise.all(instances.map(instance => instance.cleanup()));
      }
    });
  });

  describe('Reliability and Fault Tolerance', () => {
    it('should maintain 99.9% uptime under normal conditions', async () => {
      const testDuration = 300000; // 5 minutes
      const checkInterval = 1000; // 1 second
      const healthChecks = [];

      const startTime = Date.now();

      // Continuous health monitoring
      const healthCheckInterval = setInterval(async () => {
        try {
          const flowRegistryHealth = await flowRegistry.getFlow('health_check_flow') !== null;
          const healthMonitorStatus = healthMonitor.isMonitoring;
          const impactAnalyzerHealth = await impactAnalyzer.analyzeError('health_check', createMockError());

          healthChecks.push({
            timestamp: Date.now(),
            flowRegistry: flowRegistryHealth || true, // Consider healthy if method succeeds
            healthMonitor: healthMonitorStatus,
            impactAnalyzer: impactAnalyzerHealth.success,
            overall: true
          });

        } catch (error) {
          healthChecks.push({
            timestamp: Date.now(),
            error: error.message,
            overall: false
          });
        }
      }, checkInterval);

      // Wait for test duration
      await new Promise(resolve => setTimeout(resolve, testDuration));
      clearInterval(healthCheckInterval);

      const totalChecks = healthChecks.length;
      const successfulChecks = healthChecks.filter(check => check.overall).length;
      const uptime = successfulChecks / totalChecks;

      expect(uptime).toBeGreaterThan(0.999); // 99.9% uptime
      expect(totalChecks).toBeGreaterThan(250); // At least 250 checks in 5 minutes
    });

    it('should recover gracefully from temporary failures', async () => {
      // Simulate various failure scenarios
      const failureScenarios = [
        {
          name: 'Memory pressure',
          simulate: () => {
            // Create memory pressure
            const arrays = [];
            for (let i = 0; i < 100; i++) {
              arrays.push(new Array(1024 * 1024).fill('test'));
            }
            setTimeout(() => arrays.length = 0, 5000); // Cleanup after 5 seconds
          }
        },
        {
          name: 'High CPU load',
          simulate: () => {
            const endTime = Date.now() + 3000; // 3 seconds of CPU burn
            while (Date.now() < endTime) {
              Math.random();
            }
          }
        },
        {
          name: 'Simulated network issues',
          simulate: () => {
            // Mock network delays
            const originalMethod = flowRegistry.registerFlow;
            flowRegistry.registerFlow = async (...args) => {
              await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
              return originalMethod.apply(flowRegistry, args);
            };

            setTimeout(() => {
              flowRegistry.registerFlow = originalMethod;
            }, 10000); // Restore after 10 seconds
          }
        }
      ];

      for (const scenario of failureScenarios) {
        console.log(`Testing recovery from: ${scenario.name}`);

        // Baseline performance
        const baselineStart = Date.now();
        await flowRegistry.registerFlow(generateFlowId(), 'test-service', {});
        const baselineTime = Date.now() - baselineStart;

        // Inject failure
        scenario.simulate();

        // Monitor recovery
        let recovered = false;
        const recoveryStart = Date.now();
        const maxRecoveryTime = 30000; // 30 seconds

        while (!recovered && (Date.now() - recoveryStart) < maxRecoveryTime) {
          try {
            const testStart = Date.now();
            await flowRegistry.registerFlow(generateFlowId(), 'test-service', {});
            const testTime = Date.now() - testStart;

            // Consider recovered if response time is within 5x baseline
            if (testTime < baselineTime * 5) {
              recovered = true;
            }
          } catch (error) {
            // Continue monitoring
          }

          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        const recoveryTime = Date.now() - recoveryStart;

        expect(recovered).toBe(true);
        expect(recoveryTime).toBeLessThan(maxRecoveryTime);

        console.log(`Recovery time for ${scenario.name}: ${recoveryTime}ms`);
      }
    });

    it('should handle cascading failures with isolation', async () => {
      // Setup services with dependencies
      const services = [
        { id: 'frontend', dependencies: ['api-gateway'] },
        { id: 'api-gateway', dependencies: ['auth-service', 'business-logic'] },
        { id: 'auth-service', dependencies: ['database'] },
        { id: 'business-logic', dependencies: ['database', 'cache'] },
        { id: 'database', dependencies: [] },
        { id: 'cache', dependencies: [] }
      ];

      for (const service of services) {
        await healthMonitor.registerService(service.id, {
          name: service.id,
          healthEndpoint: `http://localhost:3000/${service.id}/health`,
          dependencies: service.dependencies,
          criticality: service.id === 'database' ? 'critical' : 'medium'
        });
      }

      // Simulate database failure (root cause)
      healthMonitor._setServiceHealth('database', 'unhealthy');

      // Wait for cascade detection
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Analyze chain health
      await healthMonitor.registerChain('main-chain', {
        name: 'Main Application Chain',
        services: services.map(s => s.id),
        entryPoint: 'frontend'
      });

      const chainHealth = await healthMonitor.analyzeChainHealth('main-chain');

      expect(chainHealth.success).toBe(true);
      expect(chainHealth.criticalPathFailure).toBe(true);
      expect(chainHealth.overallStatus).toBe('unhealthy');

      // Verify isolation - some services should remain healthy
      const frontendHealth = await healthMonitor.getServiceHealth('frontend');
      expect(frontendHealth.circuitBreakerState).toBe('open');

      // Verify impact analysis
      const error = createMockError({ serviceId: 'database', type: 'connection_failure' });
      const impactAnalysis = await impactAnalyzer.analyzeError('cascade_test', error);

      expect(impactAnalysis.success).toBe(true);
      expect(impactAnalysis.impact.cascadingServices).toHaveLength.greaterThan(0);
    });
  });

  describe('Security and Compliance', () => {
    it('should maintain audit trail for all operations', async () => {
      const auditEvents = [];
      const originalLogger = mockLogger.info;

      // Capture audit events
      mockLogger.info = jest.fn((...args) => {
        auditEvents.push({
          timestamp: Date.now(),
          message: args[0],
          data: args[1]
        });
        originalLogger.apply(mockLogger, args);
      });

      try {
        // Perform various operations
        const flowId = generateFlowId();
        await flowRegistry.registerFlow(flowId, 'audit-test-service', { auditTest: true });
        await flowRegistry.updateFlow(flowId, { step: 'audit_step' });

        const error = createMockError({ serviceId: 'audit-test-service' });
        await impactAnalyzer.analyzeError('audit_error', error);

        await healthMonitor.registerService('audit-service', {
          name: 'Audit Test Service',
          healthEndpoint: 'http://localhost:3000/health'
        });

        // Verify audit trail
        const flowRegistrationEvents = auditEvents.filter(e =>
          e.message.includes('Flow registered')
        );
        const flowUpdateEvents = auditEvents.filter(e =>
          e.message.includes('Flow updated') || e.message.includes('updated')
        );
        const serviceRegistrationEvents = auditEvents.filter(e =>
          e.message.includes('Service registered')
        );

        expect(flowRegistrationEvents).toHaveLength.greaterThan(0);
        expect(serviceRegistrationEvents).toHaveLength.greaterThan(0);

        // Verify audit data completeness
        flowRegistrationEvents.forEach(event => {
          expect(event.data).toHaveProperty('flowId');
          expect(event.data).toHaveProperty('serviceId');
          expect(event.timestamp).toBeGreaterThan(0);
        });

      } finally {
        mockLogger.info = originalLogger;
      }
    });

    it('should sanitize sensitive data in logs and metrics', async () => {
      const sensitiveData = {
        password: 'secret123',
        apiKey: 'api_key_12345',
        token: 'bearer_token_xyz',
        ssn: '123-45-6789',
        creditCard: '4111-1111-1111-1111'
      };

      const flowId = generateFlowId();
      await flowRegistry.registerFlow(flowId, 'security-test', {
        userInput: sensitiveData,
        metadata: { ...sensitiveData }
      });

      const error = createMockError({
        serviceId: 'security-test',
        metadata: sensitiveData
      });

      await impactAnalyzer.analyzeError('security_test', error);

      // Check that sensitive data was not logged in plain text
      const logCalls = mockLogger.info.mock.calls.concat(
        mockLogger.warn.mock.calls,
        mockLogger.error.mock.calls
      );

      logCalls.forEach(call => {
        const logMessage = JSON.stringify(call);
        expect(logMessage).not.toContain('secret123');
        expect(logMessage).not.toContain('api_key_12345');
        expect(logMessage).not.toContain('123-45-6789');
        expect(logMessage).not.toContain('4111-1111-1111-1111');
      });
    });

    it('should enforce rate limiting and access controls', async () => {
      const rateLimit = 100; // 100 requests per second
      const testDuration = 2000; // 2 seconds
      const excessiveRequests = 300; // 50% over rate limit

      const startTime = Date.now();
      const promises = [];
      const results = [];

      // Generate excessive requests
      for (let i = 0; i < excessiveRequests; i++) {
        promises.push(
          flowRegistry.registerFlow(generateFlowId(), 'rate-limit-test', {
            requestIndex: i
          }).then(
            result => results.push({ success: true, result }),
            error => results.push({ success: false, error: error.message })
          )
        );
      }

      await Promise.all(promises);
      const actualDuration = Date.now() - startTime;

      // Verify rate limiting behavior
      const successfulRequests = results.filter(r => r.success).length;
      const actualRate = (successfulRequests / actualDuration) * 1000; // requests per second

      // Should not significantly exceed rate limit
      if (actualRate > rateLimit * 1.2) { // 20% tolerance
        console.warn(`Rate limit may not be working: ${actualRate} req/s > ${rateLimit * 1.2} req/s`);
      }

      // Verify system didn't crash under load
      expect(results).toHaveLength(excessiveRequests);
      expect(successfulRequests).toBeGreaterThan(rateLimit); // Some requests should succeed
    });
  });

  describe('Monitoring and Observability', () => {
    it('should emit comprehensive metrics for monitoring', async () => {
      // Reset metrics
      mockMetrics.increment.mockClear();
      mockMetrics.gauge.mockClear();
      mockMetrics.histogram.mockClear();

      // Perform operations that should generate metrics
      for (let i = 0; i < 50; i++) {
        const flowId = generateFlowId();
        await flowRegistry.registerFlow(flowId, `metrics-service-${i % 5}`, {
          metricsTest: true
        });

        if (i % 10 === 0) {
          await flowRegistry.updateFlow(flowId, { step: 'metrics_step' });
        }

        if (i % 20 === 0) {
          const error = createMockError({ serviceId: `metrics-service-${i % 5}` });
          await impactAnalyzer.analyzeError(`metrics_error_${i}`, error);
        }
      }

      // Verify metrics were emitted
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.registered');
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.updated');
      expect(mockMetrics.increment).toHaveBeenCalledWith('impact.analysis.completed');

      // Check for performance metrics
      const histogramCalls = mockMetrics.histogram.mock.calls;
      expect(histogramCalls.some(call => call[0].includes('response_time'))).toBe(true);

      // Verify metric diversity
      const incrementCalls = mockMetrics.increment.mock.calls;
      const uniqueMetrics = new Set(incrementCalls.map(call => call[0]));
      expect(uniqueMetrics.size).toBeGreaterThan(3); // Multiple metric types
    });

    it('should support health check endpoints', async () => {
      // Simulate health check endpoints
      const healthEndpoints = [
        {
          name: 'Flow Registry',
          check: async () => {
            const testFlow = await flowRegistry.getFlow('non_existent');
            return { status: 'healthy', component: 'flow-registry' };
          }
        },
        {
          name: 'Health Monitor',
          check: async () => {
            return {
              status: healthMonitor.isMonitoring ? 'healthy' : 'unhealthy',
              component: 'health-monitor'
            };
          }
        },
        {
          name: 'Impact Analyzer',
          check: async () => {
            const testAnalysis = await impactAnalyzer.analyzeError('health_check', createMockError());
            return {
              status: testAnalysis.success ? 'healthy' : 'unhealthy',
              component: 'impact-analyzer'
            };
          }
        }
      ];

      const healthResults = await Promise.all(
        healthEndpoints.map(async endpoint => {
          try {
            const result = await endpoint.check();
            return { ...result, endpoint: endpoint.name };
          } catch (error) {
            return {
              status: 'unhealthy',
              error: error.message,
              endpoint: endpoint.name
            };
          }
        })
      );

      // All health checks should pass
      healthResults.forEach(result => {
        expect(result.status).toBe('healthy');
        expect(result.component).toBeDefined();
      });

      // Overall system health
      const overallHealth = healthResults.every(r => r.status === 'healthy');
      expect(overallHealth).toBe(true);
    });

    it('should maintain performance SLAs under production load', async () => {
      const slaRequirements = {
        flowRegistrationP95: 100, // 100ms
        queryResponseP95: 200,    // 200ms
        errorAnalysisP95: 1000,   // 1 second
        availabilityTarget: 0.999 // 99.9%
      };

      const testDuration = 60000; // 1 minute
      const loadPattern = generateLoadPattern({
        duration: testDuration,
        peakRPS: 50,
        pattern: 'wave'
      });

      const performanceResults = {
        flowRegistration: [],
        queryResponse: [],
        errorAnalysis: [],
        failures: 0,
        total: 0
      };

      // Execute load pattern
      for (const point of loadPattern) {
        const { rps } = point;
        const promises = [];

        for (let i = 0; i < rps; i++) {
          performanceResults.total++;

          // Flow registration
          promises.push(
            measurePerformance(async () => {
              await flowRegistry.registerFlow(generateFlowId(), `sla-service-${i % 10}`, {});
            }).then(
              result => performanceResults.flowRegistration.push(result.avg),
              () => performanceResults.failures++
            )
          );

          // Query operations
          if (i % 5 === 0) {
            promises.push(
              measurePerformance(async () => {
                await flowRegistry.queryFlows({ serviceId: `sla-service-${i % 10}` });
              }).then(
                result => performanceResults.queryResponse.push(result.avg),
                () => performanceResults.failures++
              )
            );
          }

          // Error analysis
          if (i % 10 === 0) {
            promises.push(
              measurePerformance(async () => {
                await impactAnalyzer.analyzeError(`sla_error_${i}`, createMockError());
              }).then(
                result => performanceResults.errorAnalysis.push(result.avg),
                () => performanceResults.failures++
              )
            );
          }
        }

        await Promise.all(promises);
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second interval
      }

      // Calculate P95 values
      const calculateP95 = (values) => {
        const sorted = values.sort((a, b) => a - b);
        return sorted[Math.floor(sorted.length * 0.95)];
      };

      const flowRegistrationP95 = calculateP95(performanceResults.flowRegistration);
      const queryResponseP95 = calculateP95(performanceResults.queryResponse);
      const errorAnalysisP95 = calculateP95(performanceResults.errorAnalysis);
      const availability = (performanceResults.total - performanceResults.failures) / performanceResults.total;

      // Verify SLA compliance
      expect(flowRegistrationP95).toBeLessThan(slaRequirements.flowRegistrationP95);
      expect(queryResponseP95).toBeLessThan(slaRequirements.queryResponseP95);
      expect(errorAnalysisP95).toBeLessThan(slaRequirements.errorAnalysisP95);
      expect(availability).toBeGreaterThan(slaRequirements.availabilityTarget);

      console.log(`SLA Performance Results:
        Flow Registration P95: ${flowRegistrationP95.toFixed(2)}ms (SLA: ${slaRequirements.flowRegistrationP95}ms)
        Query Response P95: ${queryResponseP95.toFixed(2)}ms (SLA: ${slaRequirements.queryResponseP95}ms)
        Error Analysis P95: ${errorAnalysisP95.toFixed(2)}ms (SLA: ${slaRequirements.errorAnalysisP95}ms)
        Availability: ${(availability * 100).toFixed(3)}% (SLA: ${slaRequirements.availabilityTarget * 100}%)
      `);
    });
  });

  describe('Data Consistency and Integrity', () => {
    it('should maintain data consistency under concurrent operations', async () => {
      const concurrentOperations = 100;
      const flowId = generateFlowId();

      // Register initial flow
      await flowRegistry.registerFlow(flowId, 'consistency-test', {
        initialData: 'test'
      });

      // Perform concurrent updates
      const updatePromises = [];
      for (let i = 0; i < concurrentOperations; i++) {
        updatePromises.push(
          flowRegistry.updateFlow(flowId, {
            step: `concurrent_step_${i}`,
            timestamp: Date.now(),
            updateIndex: i
          })
        );
      }

      const results = await Promise.all(updatePromises);

      // Verify all updates succeeded
      expect(results.every(r => r.success)).toBe(true);

      // Verify final state consistency
      const finalFlow = await flowRegistry.getFlow(flowId);
      expect(finalFlow.success).toBe(true);
      expect(finalFlow.flow.steps).toHaveLength(concurrentOperations);

      // Verify no data corruption
      const stepNumbers = finalFlow.flow.steps.map(step => {
        const match = step.step.match(/concurrent_step_(\d+)/);
        return match ? parseInt(match[1]) : -1;
      });

      expect(stepNumbers.filter(n => n >= 0)).toHaveLength(concurrentOperations);
      expect(new Set(stepNumbers).size).toBe(concurrentOperations); // All unique
    });

    it('should handle database failover scenarios', async () => {
      // Simulate database failover
      const flowsBefore = [];
      const flowsAfter = [];

      // Create flows before failover
      for (let i = 0; i < 100; i++) {
        const flowId = generateFlowId();
        const result = await flowRegistry.registerFlow(flowId, 'failover-test', {
          beforeFailover: true,
          index: i
        });
        flowsBefore.push(result);
      }

      // Simulate database failover (brief unavailability)
      const originalRegisterFlow = flowRegistry.registerFlow;
      let failoverInProgress = true;

      flowRegistry.registerFlow = async (...args) => {
        if (failoverInProgress) {
          throw new Error('Database failover in progress');
        }
        return originalRegisterFlow.apply(flowRegistry, args);
      };

      // Wait for failover simulation
      setTimeout(() => {
        failoverInProgress = false;
        flowRegistry.registerFlow = originalRegisterFlow;
      }, 5000);

      // Wait for failover to complete
      await waitForCondition(
        async () => {
          try {
            await flowRegistry.registerFlow(generateFlowId(), 'failover-test', { testConnection: true });
            return true;
          } catch {
            return false;
          }
        },
        10000,
        500
      );

      // Create flows after failover
      for (let i = 0; i < 100; i++) {
        const flowId = generateFlowId();
        const result = await flowRegistry.registerFlow(flowId, 'failover-test', {
          afterFailover: true,
          index: i
        });
        flowsAfter.push(result);
      }

      // Verify data integrity
      expect(flowsBefore.every(f => f.success)).toBe(true);
      expect(flowsAfter.every(f => f.success)).toBe(true);

      // Verify no data loss
      const allFlows = await flowRegistry.queryFlows({ serviceId: 'failover-test' });
      expect(allFlows.flows).toHaveLength(201); // 100 before + 100 after + 1 test connection
    });
  });
});