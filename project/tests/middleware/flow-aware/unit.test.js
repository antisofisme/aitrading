/**
 * @fileoverview Unit tests for flow-aware middleware components
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Comprehensive unit tests for all middleware components
 */

const {
  FlowTracker,
  ChainContextManager,
  FlowMetricsCollector,
  ChainEventPublisher,
  FlowContext,
  ChainContext,
  FlowEvent,
  createFlowTracker,
  createChainContextManager,
  createFlowMetricsCollector,
  createChainEventPublisher
} = require('../../../backend/shared/middleware/flow-aware');

describe('Flow-Aware Middleware Unit Tests', () => {

  describe('FlowTracker', () => {
    let flowTracker;
    let mockLogger;
    let mockReq;
    let mockRes;

    beforeEach(() => {
      mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
        debug: jest.fn()
      };

      flowTracker = createFlowTracker({
        serviceName: 'test-service',
        logger: mockLogger,
        performanceThreshold: 1
      });

      mockReq = {
        headers: {},
        method: 'GET',
        path: '/test',
        originalUrl: '/test',
        ip: '127.0.0.1'
      };

      mockRes = {
        setHeader: jest.fn(),
        end: jest.fn()
      };
    });

    test('should create flow context for new request', () => {
      const flowContext = flowTracker.createFlowContext(mockReq);

      expect(flowContext).toBeInstanceOf(FlowContext);
      expect(flowContext.flowId).toBeDefined();
      expect(flowContext.correlationId).toBeDefined();
      expect(flowContext.serviceName).toBe('test-service');
      expect(flowContext.serviceChain).toEqual([]);
    });

    test('should extract existing flow context from headers', () => {
      const existingFlowId = 'existing-flow-123';
      const existingCorrelationId = 'existing-correlation-456';

      mockReq.headers['x-flow-id'] = existingFlowId;
      mockReq.headers['x-correlation-id'] = existingCorrelationId;
      mockReq.headers['x-service-chain'] = JSON.stringify(['upstream-service']);

      const flowContext = flowTracker.createFlowContext(mockReq);

      expect(flowContext.flowId).toBe(existingFlowId);
      expect(flowContext.correlationId).toBe(existingCorrelationId);
      expect(flowContext.serviceChain).toEqual(['upstream-service']);
    });

    test('should set response headers correctly', () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456'
      });

      flowTracker.setResponseHeaders(mockRes, flowContext);

      expect(mockRes.setHeader).toHaveBeenCalledWith('x-flow-id', 'test-flow-123');
      expect(mockRes.setHeader).toHaveBeenCalledWith('x-correlation-id', 'test-correlation-456');
    });

    test('should create outgoing headers for dependency calls', () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456'
      });

      mockReq.flowContext = flowContext;

      const headers = flowTracker.createOutgoingHeaders(mockReq, 'target-service');

      expect(headers['x-flow-id']).toBe('test-flow-123');
      expect(headers['x-correlation-id']).toBe('test-correlation-456');
    });

    test('should track dependency calls', () => {
      const flowContext = new FlowContext({ serviceName: 'test-service' });
      mockReq.flowContext = flowContext;

      const dependencyMiddleware = flowTracker.trackDependency('target-service', 'http');
      dependencyMiddleware(mockReq, mockRes, () => {});

      expect(flowContext.dependencies.size).toBe(1);
      const dependency = Array.from(flowContext.dependencies)[0];
      expect(dependency.service).toBe('target-service');
      expect(dependency.type).toBe('http');
    });

    test('should add errors to flow context', () => {
      const flowContext = new FlowContext({ serviceName: 'test-service' });
      mockReq.flowContext = flowContext;

      const error = new Error('Test error');
      error.code = 'TEST_ERROR';

      flowTracker.addError(mockReq, error);

      expect(flowContext.errors).toHaveLength(1);
      expect(flowContext.errors[0].message).toBe('Test error');
      expect(flowContext.errors[0].code).toBe('TEST_ERROR');
    });
  });

  describe('ChainContextManager', () => {
    let contextManager;
    let mockLogger;

    beforeEach(() => {
      mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
        debug: jest.fn()
      };

      contextManager = createChainContextManager({
        serviceName: 'test-service',
        logger: mockLogger
      });
    });

    test('should create new chain context', () => {
      const context = new ChainContext({
        serviceName: 'test-service',
        data: { test: 'value' }
      });

      expect(context.id).toBeDefined();
      expect(context.serviceName).toBe('test-service');
      expect(context.depth).toBe(0);
      expect(context.get('test')).toBe('value');
    });

    test('should create child context correctly', () => {
      const parentContext = new ChainContext({
        serviceName: 'parent-service',
        data: { shared: 'data' }
      });

      const childContext = parentContext.createChild('child-service', {
        inheritData: true
      });

      expect(childContext.parentId).toBe(parentContext.id);
      expect(childContext.rootId).toBe(parentContext.rootId);
      expect(childContext.depth).toBe(1);
      expect(childContext.serviceName).toBe('child-service');
      expect(childContext.get('shared')).toBe('data');
    });

    test('should serialize and deserialize context', () => {
      const originalContext = new ChainContext({
        serviceName: 'test-service',
        data: { key: 'value' },
        metadata: { test: true }
      });

      const serialized = originalContext.serialize();
      const deserializedContext = ChainContext.deserialize(serialized);

      expect(deserializedContext.id).toBe(originalContext.id);
      expect(deserializedContext.serviceName).toBe(originalContext.serviceName);
      expect(deserializedContext.data).toEqual(originalContext.data);
      expect(deserializedContext.metadata).toEqual(originalContext.metadata);
    });

    test('should validate context size limits', () => {
      const context = new ChainContext({ serviceName: 'test-service' });

      // Add large amount of data
      const largeData = 'x'.repeat(10000);

      expect(() => {
        context.set('large', largeData);
      }).toThrow('Context size exceeded limit');
    });

    test('should handle context expiration', () => {
      const context = new ChainContext({
        serviceName: 'test-service',
        ttl: 100 // 100ms TTL
      });

      expect(context.isExpired()).toBe(false);

      // Wait for expiration
      return new Promise(resolve => {
        setTimeout(() => {
          expect(context.isExpired()).toBe(true);
          resolve();
        }, 150);
      });
    });
  });

  describe('FlowMetricsCollector', () => {
    let metricsCollector;
    let mockLogger;

    beforeEach(() => {
      mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
        debug: jest.fn()
      };

      metricsCollector = createFlowMetricsCollector({
        serviceName: 'test-service',
        logger: mockLogger,
        enableRealTimeMetrics: false
      });
    });

    afterEach(() => {
      metricsCollector.stop();
    });

    test('should create and track metrics', () => {
      const counter = metricsCollector.createCounter('test_counter', 'Test counter', ['label']);

      counter.increment(5);
      expect(counter.value).toBe(5);

      counter.increment(3);
      expect(counter.value).toBe(8);
    });

    test('should calculate metric statistics', () => {
      const counter = metricsCollector.createCounter('test_counter', 'Test counter');

      counter.addSample(10);
      counter.addSample(20);
      counter.addSample(30);

      const stats = counter.getStats();
      expect(stats.count).toBe(3);
      expect(stats.min).toBe(10);
      expect(stats.max).toBe(30);
      expect(stats.avg).toBe(20);
      expect(stats.sum).toBe(60);
    });

    test('should collect flow metrics from context', () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456'
      });

      flowContext.metrics.duration = 150;
      flowContext.errors = [];
      flowContext.serviceChain = ['service1', 'service2'];

      metricsCollector.collect(flowContext);

      const metrics = metricsCollector.getAllMetrics();
      expect(metrics.counters).toBeDefined();
      expect(metrics.timers).toBeDefined();
    });

    test('should handle metric labels correctly', () => {
      metricsCollector.incrementCounter('test_requests', 1, { status: 'success', service: 'test' });
      metricsCollector.incrementCounter('test_requests', 1, { status: 'error', service: 'test' });

      const metrics = metricsCollector.getAllMetrics();
      const counterKeys = Object.keys(metrics.counters);

      // Should have separate metrics for different label combinations
      expect(counterKeys.length).toBeGreaterThan(1);
      expect(counterKeys.some(key => key.includes('status=success'))).toBe(true);
      expect(counterKeys.some(key => key.includes('status=error'))).toBe(true);
    });
  });

  describe('ChainEventPublisher', () => {
    let eventPublisher;
    let mockLogger;

    beforeEach(() => {
      mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
        debug: jest.fn()
      };

      eventPublisher = createChainEventPublisher({
        serviceName: 'test-service',
        logger: mockLogger,
        enableBuffering: false // Disable buffering for unit tests
      });
    });

    afterEach(async () => {
      await eventPublisher.stop();
    });

    test('should create and serialize flow events', () => {
      const eventData = { message: 'test event', timestamp: Date.now() };
      const event = new FlowEvent('test.event', eventData, {
        serviceName: 'test-service',
        flowId: 'test-flow-123'
      });

      expect(event.type).toBe('test.event');
      expect(event.data).toEqual(eventData);
      expect(event.serviceName).toBe('test-service');
      expect(event.flowId).toBe('test-flow-123');

      const serialized = event.serialize();
      expect(serialized.type).toBe('test.event');
      expect(serialized.data).toEqual(eventData);
    });

    test('should publish events successfully', async () => {
      const eventId = await eventPublisher.publish('test.event', {
        message: 'test message'
      });

      expect(eventId).toBeDefined();
      expect(typeof eventId).toBe('string');
    });

    test('should publish flow start events', async () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456'
      });

      const eventId = await eventPublisher.publishFlowStart(flowContext);
      expect(eventId).toBeDefined();
    });

    test('should publish flow complete events', async () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456'
      });

      flowContext.complete();

      const eventId = await eventPublisher.publishFlowComplete(flowContext);
      expect(eventId).toBeDefined();
    });

    test('should publish error events', async () => {
      const flowContext = new FlowContext({
        serviceName: 'test-service',
        flowId: 'test-flow-123'
      });

      const error = new Error('Test error');
      error.code = 'TEST_ERROR';

      const eventId = await eventPublisher.publishError(flowContext, error);
      expect(eventId).toBeDefined();
    });

    test('should handle event correlation', async () => {
      const correlationId = 'test-correlation-123';

      await eventPublisher.publish('test.event1', { data: 1 }, { correlationId });
      await eventPublisher.publish('test.event2', { data: 2 }, { correlationId });

      const correlatedEvents = eventPublisher.getCorrelatedEvents(correlationId);
      expect(correlatedEvents).toHaveLength(2);
      expect(correlatedEvents[0].data.data).toBe(1);
      expect(correlatedEvents[1].data.data).toBe(2);
    });

    test('should provide publisher statistics', () => {
      const stats = eventPublisher.getStats();

      expect(stats).toHaveProperty('eventsPublished');
      expect(stats).toHaveProperty('eventsDropped');
      expect(stats).toHaveProperty('channels');
      expect(typeof stats.eventsPublished).toBe('number');
    });
  });

  describe('FlowContext', () => {
    test('should generate unique flow and correlation IDs', () => {
      const context1 = new FlowContext({ serviceName: 'service1' });
      const context2 = new FlowContext({ serviceName: 'service2' });

      expect(context1.flowId).not.toBe(context2.flowId);
      expect(context1.correlationId).not.toBe(context2.correlationId);
    });

    test('should add services to chain with validation', () => {
      const context = new FlowContext({ serviceName: 'service1' });

      context.addToChain('service2');
      context.addToChain('service3');
      context.addToChain('service2'); // Duplicate should not be added again

      expect(context.serviceChain).toEqual(['service2', 'service3']);
    });

    test('should prevent infinite service chains', () => {
      const context = new FlowContext({ serviceName: 'service1' });

      // Add maximum allowed services
      for (let i = 0; i < 50; i++) {
        context.addToChain(`service${i}`);
      }

      // Adding one more should throw error
      expect(() => {
        context.addToChain('overflow-service');
      }).toThrow('Service chain exceeded maximum length');
    });

    test('should track dependencies correctly', () => {
      const context = new FlowContext({ serviceName: 'service1' });

      context.addDependency('database', 'sql');
      context.addDependency('cache', 'redis');
      context.addDependency('api', 'http');

      expect(context.dependencies.size).toBe(3);

      const deps = Array.from(context.dependencies);
      expect(deps.some(d => d.service === 'database' && d.type === 'sql')).toBe(true);
      expect(deps.some(d => d.service === 'cache' && d.type === 'redis')).toBe(true);
      expect(deps.some(d => d.service === 'api' && d.type === 'http')).toBe(true);
    });

    test('should complete flow tracking with metrics', () => {
      const context = new FlowContext({ serviceName: 'service1' });

      // Simulate some processing time
      setTimeout(() => {
        context.complete();

        expect(context.metrics.endTime).toBeDefined();
        expect(context.metrics.duration).toBeGreaterThan(0);
        expect(context.metrics.finalMemoryUsage).toBeDefined();
        expect(context.metrics.finalCpuUsage).toBeDefined();
      }, 10);
    });

    test('should convert to/from headers correctly', () => {
      const originalContext = new FlowContext({
        serviceName: 'service1',
        flowId: 'test-flow-123',
        correlationId: 'test-correlation-456',
        parentFlowId: 'parent-flow-789',
        userId: 'user123',
        sessionId: 'session456'
      });

      originalContext.addToChain('service1');
      originalContext.addToChain('service2');

      const headers = originalContext.toHeaders();
      const recreatedContext = FlowContext.fromHeaders(headers, 'service3');

      expect(recreatedContext.flowId).toBe(originalContext.flowId);
      expect(recreatedContext.correlationId).toBe(originalContext.correlationId);
      expect(recreatedContext.parentFlowId).toBe(originalContext.parentFlowId);
      expect(recreatedContext.userId).toBe(originalContext.userId);
      expect(recreatedContext.sessionId).toBe(originalContext.sessionId);
      expect(recreatedContext.serviceChain).toEqual(originalContext.serviceChain);
    });
  });

  describe('Performance Validation', () => {
    test('should meet performance requirements', () => {
      const iterations = 1000;
      const measurements = [];

      for (let i = 0; i < iterations; i++) {
        const startTime = performance.now();

        // Create flow context (most expensive operation)
        const context = new FlowContext({
          serviceName: 'perf-test-service',
          metadata: { path: '/test', method: 'GET' },
          tags: { environment: 'test' }
        });

        context.addToChain('service1');
        context.addDependency('db', 'sql');
        context.complete();

        const endTime = performance.now();
        measurements.push(endTime - startTime);
      }

      const avgTime = measurements.reduce((a, b) => a + b, 0) / measurements.length;
      const maxTime = Math.max(...measurements);
      const p95Time = measurements.sort((a, b) => a - b)[Math.floor(measurements.length * 0.95)];

      console.log(`Average context creation time: ${avgTime.toFixed(3)}ms`);
      console.log(`Maximum context creation time: ${maxTime.toFixed(3)}ms`);
      console.log(`P95 context creation time: ${p95Time.toFixed(3)}ms`);

      // Performance requirements
      expect(avgTime).toBeLessThan(0.1); // Less than 0.1ms average
      expect(p95Time).toBeLessThan(0.5); // Less than 0.5ms for P95
      expect(maxTime).toBeLessThan(1); // Less than 1ms maximum
    });
  });
});