/**
 * Unit Tests for FlowRegistry Component
 * Tests flow tracking, registration, and lifecycle management
 */

const FlowRegistry = require('@mocks/flow-registry');
const { generateFlowId, generateServiceId } = require('@utils/test-helpers');

describe('FlowRegistry Unit Tests', () => {
  let flowRegistry;
  let mockLogger;
  let mockMetrics;

  beforeEach(() => {
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

    flowRegistry = new FlowRegistry({
      logger: mockLogger,
      metrics: mockMetrics,
      maxFlows: 10000,
      retentionPeriod: 3600000 // 1 hour
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Flow Registration', () => {
    it('should register a new flow successfully', async () => {
      const flowId = generateFlowId();
      const serviceId = generateServiceId();
      const metadata = {
        operation: 'trade_execution',
        userId: 'user123',
        symbol: 'BTCUSD'
      };

      const result = await flowRegistry.registerFlow(flowId, serviceId, metadata);

      expect(result.success).toBe(true);
      expect(result.flowId).toBe(flowId);
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.registered');
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('Flow registered'),
        expect.objectContaining({ flowId, serviceId })
      );
    });

    it('should handle duplicate flow registration gracefully', async () => {
      const flowId = generateFlowId();
      const serviceId = generateServiceId();

      // Register flow first time
      await flowRegistry.registerFlow(flowId, serviceId, {});

      // Try to register same flow again
      const result = await flowRegistry.registerFlow(flowId, serviceId, {});

      expect(result.success).toBe(false);
      expect(result.error).toContain('already registered');
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Duplicate flow registration'),
        expect.objectContaining({ flowId })
      );
    });

    it('should validate flow registration parameters', async () => {
      // Test invalid flowId
      const result1 = await flowRegistry.registerFlow(null, 'service1', {});
      expect(result1.success).toBe(false);
      expect(result1.error).toContain('Invalid flowId');

      // Test invalid serviceId
      const result2 = await flowRegistry.registerFlow('flow1', '', {});
      expect(result2.success).toBe(false);
      expect(result2.error).toContain('Invalid serviceId');
    });

    it('should enforce maximum flows limit', async () => {
      const smallRegistry = new FlowRegistry({
        logger: mockLogger,
        metrics: mockMetrics,
        maxFlows: 2
      });

      // Register flows up to limit
      await smallRegistry.registerFlow('flow1', 'service1', {});
      await smallRegistry.registerFlow('flow2', 'service2', {});

      // Try to register one more
      const result = await smallRegistry.registerFlow('flow3', 'service3', {});

      expect(result.success).toBe(false);
      expect(result.error).toContain('Maximum flows exceeded');
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.limit_exceeded');
    });
  });

  describe('Flow Tracking', () => {
    let flowId, serviceId;

    beforeEach(async () => {
      flowId = generateFlowId();
      serviceId = generateServiceId();
      await flowRegistry.registerFlow(flowId, serviceId, {});
    });

    it('should track flow progress updates', async () => {
      const update = {
        step: 'validation',
        status: 'in_progress',
        timestamp: Date.now(),
        data: { validationRules: 5 }
      };

      const result = await flowRegistry.updateFlow(flowId, update);

      expect(result.success).toBe(true);
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.updated');

      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.steps).toHaveLength(1);
      expect(flow.steps[0]).toMatchObject(update);
    });

    it('should handle flow errors correctly', async () => {
      const error = {
        step: 'execution',
        status: 'error',
        error: new Error('Trade execution failed'),
        timestamp: Date.now()
      };

      const result = await flowRegistry.addError(flowId, error);

      expect(result.success).toBe(true);
      expect(mockMetrics.increment).toHaveBeenCalledWith('flow.error_added');

      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.errors).toHaveLength(1);
      expect(flow.status).toBe('error');
    });

    it('should calculate flow duration correctly', async () => {
      const startTime = Date.now() - 1000; // 1 second ago

      // Update flow registry with start time
      await flowRegistry.updateFlow(flowId, {
        step: 'started',
        status: 'in_progress',
        timestamp: startTime
      });

      // Complete the flow
      await flowRegistry.completeFlow(flowId, {
        status: 'completed',
        timestamp: Date.now()
      });

      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.duration).toBeGreaterThan(900); // At least 900ms
      expect(flow.duration).toBeLessThan(2000); // Less than 2 seconds
    });

    it('should maintain flow state consistency', async () => {
      // Add multiple updates
      await flowRegistry.updateFlow(flowId, {
        step: 'validation',
        status: 'completed',
        timestamp: Date.now() - 500
      });

      await flowRegistry.updateFlow(flowId, {
        step: 'execution',
        status: 'in_progress',
        timestamp: Date.now()
      });

      const flow = await flowRegistry.getFlow(flowId);
      expect(flow.steps).toHaveLength(2);
      expect(flow.currentStep).toBe('execution');
      expect(flow.status).toBe('in_progress');
    });
  });

  describe('Flow Querying', () => {
    beforeEach(async () => {
      // Setup test flows
      const flows = [
        { id: 'flow1', service: 'service1', status: 'completed' },
        { id: 'flow2', service: 'service1', status: 'error' },
        { id: 'flow3', service: 'service2', status: 'in_progress' }
      ];

      for (const flow of flows) {
        await flowRegistry.registerFlow(flow.id, flow.service, {});
        if (flow.status !== 'in_progress') {
          await flowRegistry.completeFlow(flow.id, { status: flow.status });
        }
      }
    });

    it('should query flows by service', async () => {
      const result = await flowRegistry.getFlowsByService('service1');

      expect(result.success).toBe(true);
      expect(result.flows).toHaveLength(2);
      expect(result.flows.every(f => f.serviceId === 'service1')).toBe(true);
    });

    it('should query flows by status', async () => {
      const result = await flowRegistry.getFlowsByStatus('error');

      expect(result.success).toBe(true);
      expect(result.flows).toHaveLength(1);
      expect(result.flows[0].id).toBe('flow2');
    });

    it('should query flows by time range', async () => {
      const now = Date.now();
      const oneHourAgo = now - 3600000;

      const result = await flowRegistry.getFlowsByTimeRange(oneHourAgo, now);

      expect(result.success).toBe(true);
      expect(result.flows).toHaveLength(3); // All flows within range
    });

    it('should handle complex flow queries', async () => {
      const query = {
        serviceId: 'service1',
        status: ['completed', 'error'],
        timeRange: {
          start: Date.now() - 3600000,
          end: Date.now()
        },
        limit: 10,
        offset: 0
      };

      const result = await flowRegistry.queryFlows(query);

      expect(result.success).toBe(true);
      expect(result.flows).toHaveLength(2);
      expect(result.total).toBe(2);
    });
  });

  describe('Flow Cleanup', () => {
    it('should cleanup expired flows', async () => {
      const oldFlowId = generateFlowId();
      const recentFlowId = generateFlowId();

      // Create old flow (simulate 2 hours ago)
      await flowRegistry.registerFlow(oldFlowId, 'service1', {});
      const oldFlow = await flowRegistry.getFlow(oldFlowId);
      oldFlow.timestamp = Date.now() - 7200000; // 2 hours ago

      // Create recent flow
      await flowRegistry.registerFlow(recentFlowId, 'service2', {});

      const cleanupResult = await flowRegistry.cleanup();

      expect(cleanupResult.success).toBe(true);
      expect(cleanupResult.cleanedCount).toBe(1);
      expect(mockMetrics.gauge).toHaveBeenCalledWith('flow.active_count', 1);

      // Verify old flow is gone, recent flow remains
      const oldFlowResult = await flowRegistry.getFlow(oldFlowId);
      expect(oldFlowResult.success).toBe(false);

      const recentFlowResult = await flowRegistry.getFlow(recentFlowId);
      expect(recentFlowResult.success).toBe(true);
    });

    it('should handle cleanup with retention policy', async () => {
      const shortRetentionRegistry = new FlowRegistry({
        logger: mockLogger,
        metrics: mockMetrics,
        retentionPeriod: 1000 // 1 second
      });

      const flowId = generateFlowId();
      await shortRetentionRegistry.registerFlow(flowId, 'service1', {});

      // Wait for retention period
      await new Promise(resolve => setTimeout(resolve, 1100));

      const cleanupResult = await shortRetentionRegistry.cleanup();
      expect(cleanupResult.cleanedCount).toBe(1);
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle high-frequency flow registration', async () => {
      const startTime = Date.now();
      const flowCount = 1000;
      const promises = [];

      for (let i = 0; i < flowCount; i++) {
        promises.push(
          flowRegistry.registerFlow(`flow_${i}`, `service_${i % 10}`, {
            batchId: Math.floor(i / 100)
          })
        );
      }

      const results = await Promise.all(promises);
      const endTime = Date.now();
      const duration = endTime - startTime;

      // All registrations should succeed
      expect(results.every(r => r.success)).toBe(true);

      // Should complete within reasonable time (less than 5 seconds)
      expect(duration).toBeLessThan(5000);

      // Should handle concurrent registrations efficiently
      const throughput = flowCount / (duration / 1000);
      expect(throughput).toBeGreaterThan(200); // At least 200 flows/second
    });

    it('should maintain performance under memory pressure', async () => {
      const largeMetadata = {
        largeData: 'x'.repeat(10000) // 10KB of data per flow
      };

      // Register many flows with large metadata
      for (let i = 0; i < 500; i++) {
        await flowRegistry.registerFlow(`flow_${i}`, 'service1', largeMetadata);
      }

      const startTime = Date.now();
      const result = await flowRegistry.getFlowsByService('service1');
      const queryTime = Date.now() - startTime;

      expect(result.success).toBe(true);
      expect(result.flows).toHaveLength(500);
      expect(queryTime).toBeLessThan(1000); // Should complete within 1 second
    });
  });

  describe('Error Handling', () => {
    it('should handle database connection errors gracefully', async () => {
      // Mock database error
      flowRegistry._storage = {
        save: jest.fn().mockRejectedValue(new Error('Database connection lost'))
      };

      const result = await flowRegistry.registerFlow('flow1', 'service1', {});

      expect(result.success).toBe(false);
      expect(result.error).toContain('Database connection lost');
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Flow registration failed'),
        expect.any(Object)
      );
    });

    it('should handle invalid flow data gracefully', async () => {
      const invalidUpdate = {
        step: null,
        status: 'invalid_status',
        timestamp: 'not_a_number'
      };

      const result = await flowRegistry.updateFlow('nonexistent_flow', invalidUpdate);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should recover from memory overflow conditions', async () => {
      // Simulate memory pressure
      const originalMaxFlows = flowRegistry.config.maxFlows;
      flowRegistry.config.maxFlows = 5;

      // Fill up to capacity
      for (let i = 0; i < 5; i++) {
        await flowRegistry.registerFlow(`flow_${i}`, 'service1', {});
      }

      // Try to add one more (should trigger cleanup)
      const result = await flowRegistry.registerFlow('overflow_flow', 'service1', {});

      // Should either succeed after cleanup or fail gracefully
      expect(result).toHaveProperty('success');
      if (!result.success) {
        expect(result.error).toContain('Maximum flows exceeded');
      }

      flowRegistry.config.maxFlows = originalMaxFlows;
    });
  });
});