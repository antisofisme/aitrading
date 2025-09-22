/**
 * Mock Implementation of FlowRegistry for Testing
 * Provides a realistic simulation of flow tracking capabilities
 */

const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

class MockFlowRegistry extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      maxFlows: config.maxFlows || 10000,
      retentionPeriod: config.retentionPeriod || 3600000, // 1 hour
      indexingStrategy: config.indexingStrategy || 'standard',
      memoryManagement: config.memoryManagement || 'standard',
      persistenceMode: config.persistenceMode || 'immediate',
      logger: config.logger || this._createMockLogger(),
      metrics: config.metrics || this._createMockMetrics(),
      ...config
    };

    // In-memory storage
    this.flows = new Map();
    this.serviceIndex = new Map();
    this.statusIndex = new Map();
    this.timeIndex = new Map();

    // Performance tracking
    this.operationTimes = {
      registration: [],
      lookup: [],
      update: [],
      query: []
    };

    // State management
    this.isInitialized = false;
    this.cleanupInterval = null;
  }

  async initialize() {
    if (this.isInitialized) return { success: true };

    try {
      // Initialize indexes
      this._initializeIndexes();

      // Start cleanup interval
      this._startCleanupInterval();

      this.isInitialized = true;
      this.config.logger.info('MockFlowRegistry initialized');

      return { success: true };
    } catch (error) {
      this.config.logger.error('Failed to initialize MockFlowRegistry', error);
      return { success: false, error: error.message };
    }
  }

  async cleanup() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    this.flows.clear();
    this._clearIndexes();
    this.isInitialized = false;

    return { success: true };
  }

  async registerFlow(flowId, serviceId, metadata = {}) {
    const startTime = Date.now();

    try {
      // Validate inputs
      if (!flowId || typeof flowId !== 'string') {
        return { success: false, error: 'Invalid flowId' };
      }

      if (!serviceId || typeof serviceId !== 'string') {
        return { success: false, error: 'Invalid serviceId' };
      }

      // Check if flow already exists
      if (this.flows.has(flowId)) {
        this.config.logger.warn('Duplicate flow registration attempted', { flowId });
        return { success: false, error: 'Flow already registered' };
      }

      // Check flow limit
      if (this.flows.size >= this.config.maxFlows) {
        this.config.metrics.increment('flow.limit_exceeded');
        return { success: false, error: 'Maximum flows exceeded' };
      }

      // Create flow object
      const flow = {
        id: flowId,
        serviceId,
        status: 'pending',
        timestamp: Date.now(),
        metadata: { ...metadata },
        steps: [],
        errors: [],
        currentStep: null,
        duration: null,
        createdAt: new Date().toISOString()
      };

      // Store flow
      this.flows.set(flowId, flow);

      // Update indexes
      this._updateIndexes(flow, 'add');

      // Emit event
      this.emit('flowRegistered', { flowId, serviceId, flow });

      // Record metrics
      this.config.metrics.increment('flow.registered');
      this.config.logger.info('Flow registered successfully', { flowId, serviceId });

      // Track performance
      this.operationTimes.registration.push(Date.now() - startTime);

      return { success: true, flowId, flow };

    } catch (error) {
      this.config.logger.error('Flow registration failed', { flowId, serviceId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async getFlow(flowId) {
    const startTime = Date.now();

    try {
      if (!flowId) {
        return { success: false, error: 'FlowId is required' };
      }

      const flow = this.flows.get(flowId);

      if (!flow) {
        return { success: false, error: 'Flow not found' };
      }

      // Track performance
      this.operationTimes.lookup.push(Date.now() - startTime);

      return { success: true, flow: { ...flow } };

    } catch (error) {
      this.config.logger.error('Flow lookup failed', { flowId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async updateFlow(flowId, update) {
    const startTime = Date.now();

    try {
      const flow = this.flows.get(flowId);

      if (!flow) {
        return { success: false, error: 'Flow not found' };
      }

      // Validate update
      if (!update || typeof update !== 'object') {
        return { success: false, error: 'Invalid update object' };
      }

      // Update flow
      if (update.step) {
        flow.steps.push({
          step: update.step,
          status: update.status || 'completed',
          timestamp: update.timestamp || Date.now(),
          serviceId: flow.serviceId,
          data: update.data || {},
          ...update
        });
        flow.currentStep = update.step;
      }

      if (update.status) {
        const oldStatus = flow.status;
        flow.status = update.status;

        // Update status index
        this._updateStatusIndex(flow, oldStatus, update.status);
      }

      flow.lastUpdated = Date.now();

      // Calculate duration if completed
      if (update.status === 'completed' || update.status === 'error') {
        flow.duration = flow.lastUpdated - flow.timestamp;
      }

      // Emit event
      this.emit('flowUpdated', { flowId, update, flow });

      // Record metrics
      this.config.metrics.increment('flow.updated');

      // Track performance
      this.operationTimes.update.push(Date.now() - startTime);

      return { success: true, flow };

    } catch (error) {
      this.config.logger.error('Flow update failed', { flowId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async addError(flowId, error) {
    try {
      const flow = this.flows.get(flowId);

      if (!flow) {
        return { success: false, error: 'Flow not found' };
      }

      const errorEntry = {
        id: uuidv4(),
        timestamp: Date.now(),
        ...error
      };

      flow.errors.push(errorEntry);
      flow.status = 'error';
      flow.lastUpdated = Date.now();

      // Update status index
      this._updateStatusIndex(flow, flow.status, 'error');

      // Emit event
      this.emit('flowError', { flowId, error: errorEntry, flow });

      // Record metrics
      this.config.metrics.increment('flow.error_added');

      return { success: true, errorId: errorEntry.id };

    } catch (err) {
      this.config.logger.error('Failed to add error to flow', { flowId, error: err.message });
      return { success: false, error: err.message };
    }
  }

  async completeFlow(flowId, completionData = {}) {
    try {
      const flow = this.flows.get(flowId);

      if (!flow) {
        return { success: false, error: 'Flow not found' };
      }

      flow.status = completionData.status || 'completed';
      flow.completedAt = Date.now();
      flow.duration = flow.completedAt - flow.timestamp;
      flow.completionData = completionData;

      // Update indexes
      this._updateStatusIndex(flow, flow.status, flow.status);

      // Emit event
      this.emit('flowCompleted', { flowId, completionData, flow });

      return { success: true, flow };

    } catch (error) {
      this.config.logger.error('Flow completion failed', { flowId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async queryFlows(query = {}) {
    const startTime = Date.now();

    try {
      let flows = Array.from(this.flows.values());

      // Apply filters
      if (query.serviceId) {
        flows = flows.filter(flow => flow.serviceId === query.serviceId);
      }

      if (query.status) {
        const statuses = Array.isArray(query.status) ? query.status : [query.status];
        flows = flows.filter(flow => statuses.includes(flow.status));
      }

      if (query.timeRange) {
        const { start, end } = query.timeRange;
        flows = flows.filter(flow => {
          return flow.timestamp >= start && flow.timestamp <= end;
        });
      }

      if (query.priority && query.priority.$gte !== undefined) {
        flows = flows.filter(flow => {
          return flow.metadata.priority >= query.priority.$gte;
        });
      }

      // Apply sorting
      if (query.sortBy) {
        flows.sort((a, b) => {
          const aVal = this._getNestedValue(a, query.sortBy);
          const bVal = this._getNestedValue(b, query.sortBy);
          return query.sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
        });
      }

      // Apply pagination
      const total = flows.length;
      const offset = query.offset || 0;
      const limit = query.limit || flows.length;

      flows = flows.slice(offset, offset + limit);

      // Track performance
      this.operationTimes.query.push(Date.now() - startTime);

      return {
        success: true,
        flows,
        total,
        offset,
        limit
      };

    } catch (error) {
      this.config.logger.error('Flow query failed', { query, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async getFlowsByService(serviceId) {
    return this.queryFlows({ serviceId });
  }

  async getFlowsByStatus(status) {
    return this.queryFlows({ status });
  }

  async getFlowsByTimeRange(start, end) {
    return this.queryFlows({ timeRange: { start, end } });
  }

  async getAggregateMetrics(options = {}) {
    try {
      const flows = Array.from(this.flows.values());
      const timeWindow = options.timeWindow || 3600000; // 1 hour
      const now = Date.now();
      const cutoff = now - timeWindow;

      const recentFlows = flows.filter(flow => flow.timestamp >= cutoff);

      const metrics = {
        totalFlows: recentFlows.length,
        byStatus: {},
        byService: {},
        bySymbol: {},
        averageProcessingTime: 0,
        p95ProcessingTime: 0,
        errorRate: 0
      };

      // Group by status
      recentFlows.forEach(flow => {
        metrics.byStatus[flow.status] = (metrics.byStatus[flow.status] || 0) + 1;

        // Group by service
        metrics.byService[flow.serviceId] = (metrics.byService[flow.serviceId] || 0) + 1;

        // Group by symbol if available
        if (flow.metadata.symbol) {
          metrics.bySymbol[flow.metadata.symbol] = (metrics.bySymbol[flow.metadata.symbol] || 0) + 1;
        }
      });

      // Calculate processing times
      const completedFlows = recentFlows.filter(flow => flow.duration);
      if (completedFlows.length > 0) {
        const durations = completedFlows.map(flow => flow.duration).sort((a, b) => a - b);
        metrics.averageProcessingTime = durations.reduce((a, b) => a + b, 0) / durations.length;
        metrics.p95ProcessingTime = durations[Math.floor(durations.length * 0.95)];
      }

      // Calculate error rate
      const errorFlows = recentFlows.filter(flow => flow.status === 'error').length;
      metrics.errorRate = recentFlows.length > 0 ? errorFlows / recentFlows.length : 0;

      return { success: true, metrics };

    } catch (error) {
      this.config.logger.error('Failed to get aggregate metrics', { error: error.message });
      return { success: false, error: error.message };
    }
  }

  async persistFlowsBatch(flows) {
    const startTime = Date.now();

    try {
      // Simulate batch persistence
      await new Promise(resolve => setTimeout(resolve, flows.length / 100)); // Simulate I/O

      for (const flowData of flows) {
        if (flowData.id && !this.flows.has(flowData.id)) {
          const flow = {
            id: flowData.id,
            serviceId: flowData.serviceId,
            status: 'pending',
            timestamp: flowData.timestamp || Date.now(),
            metadata: flowData.data || {},
            steps: [],
            errors: [],
            createdAt: new Date().toISOString()
          };

          this.flows.set(flow.id, flow);
          this._updateIndexes(flow, 'add');
        }
      }

      const duration = Date.now() - startTime;
      const throughput = (flows.length / duration) * 1000; // flows per second

      return {
        success: true,
        persistedCount: flows.length,
        duration,
        throughput
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async runBenchmark(loadPattern) {
    const benchmarkResults = {
      flowRegistrationLatency: { p95: 0, avg: 0 },
      queryResponseTime: { p95: 0, avg: 0 },
      healthCheckLatency: { p95: 0, avg: 0 },
      impactAnalysisTime: { p95: 0, avg: 0 },
      memoryUsagePerFlow: 0,
      errorRate: 0,
      systemStability: {
        cpuSpikes: 0,
        memoryLeaks: 0,
        networkTimeouts: 0
      }
    };

    try {
      // Simulate benchmark execution
      await new Promise(resolve => setTimeout(resolve, 100));

      // Calculate metrics from operation times
      if (this.operationTimes.registration.length > 0) {
        const regTimes = this.operationTimes.registration.sort((a, b) => a - b);
        benchmarkResults.flowRegistrationLatency.avg = regTimes.reduce((a, b) => a + b, 0) / regTimes.length;
        benchmarkResults.flowRegistrationLatency.p95 = regTimes[Math.floor(regTimes.length * 0.95)];
      }

      if (this.operationTimes.query.length > 0) {
        const queryTimes = this.operationTimes.query.sort((a, b) => a - b);
        benchmarkResults.queryResponseTime.avg = queryTimes.reduce((a, b) => a + b, 0) / queryTimes.length;
        benchmarkResults.queryResponseTime.p95 = queryTimes[Math.floor(queryTimes.length * 0.95)];
      }

      // Estimate memory usage
      const memUsage = process.memoryUsage();
      benchmarkResults.memoryUsagePerFlow = this.flows.size > 0 ? memUsage.heapUsed / this.flows.size : 0;

      // Calculate error rate
      const totalFlows = this.flows.size;
      const errorFlows = Array.from(this.flows.values()).filter(f => f.status === 'error').length;
      benchmarkResults.errorRate = totalFlows > 0 ? errorFlows / totalFlows : 0;

      return benchmarkResults;

    } catch (error) {
      throw new Error(`Benchmark failed: ${error.message}`);
    }
  }

  // Private helper methods
  _initializeIndexes() {
    this.serviceIndex.clear();
    this.statusIndex.clear();
    this.timeIndex.clear();
  }

  _clearIndexes() {
    this.serviceIndex.clear();
    this.statusIndex.clear();
    this.timeIndex.clear();
  }

  _updateIndexes(flow, operation) {
    if (operation === 'add') {
      // Service index
      if (!this.serviceIndex.has(flow.serviceId)) {
        this.serviceIndex.set(flow.serviceId, new Set());
      }
      this.serviceIndex.get(flow.serviceId).add(flow.id);

      // Status index
      if (!this.statusIndex.has(flow.status)) {
        this.statusIndex.set(flow.status, new Set());
      }
      this.statusIndex.get(flow.status).add(flow.id);

      // Time index (hour buckets)
      const hourBucket = Math.floor(flow.timestamp / 3600000) * 3600000;
      if (!this.timeIndex.has(hourBucket)) {
        this.timeIndex.set(hourBucket, new Set());
      }
      this.timeIndex.get(hourBucket).add(flow.id);
    }
  }

  _updateStatusIndex(flow, oldStatus, newStatus) {
    if (oldStatus && this.statusIndex.has(oldStatus)) {
      this.statusIndex.get(oldStatus).delete(flow.id);
    }

    if (!this.statusIndex.has(newStatus)) {
      this.statusIndex.set(newStatus, new Set());
    }
    this.statusIndex.get(newStatus).add(flow.id);
  }

  _startCleanupInterval() {
    this.cleanupInterval = setInterval(async () => {
      await this.cleanup();
    }, 300000); // 5 minutes
  }

  _getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current && current[key], obj);
  }

  _createMockLogger() {
    return {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };
  }

  _createMockMetrics() {
    return {
      increment: jest.fn(),
      gauge: jest.fn(),
      histogram: jest.fn(),
      timer: jest.fn()
    };
  }
}

module.exports = MockFlowRegistry;