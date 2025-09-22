/**
 * @fileoverview Flow Metrics Collector for real-time performance and error metrics
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Collects, aggregates, and reports flow metrics with real-time analytics,
 * performance tracking, and error correlation capabilities.
 */

const { EventEmitter } = require('events');
const { performance } = require('perf_hooks');

// =============================================================================
// METRICS CONSTANTS
// =============================================================================

const METRIC_TYPES = {
  COUNTER: 'counter',
  GAUGE: 'gauge',
  HISTOGRAM: 'histogram',
  TIMER: 'timer'
};

const COLLECTION_INTERVALS = {
  REAL_TIME: 1000,      // 1 second
  FAST: 5000,           // 5 seconds
  NORMAL: 30000,        // 30 seconds
  SLOW: 60000           // 1 minute
};

const RETENTION_PERIODS = {
  REAL_TIME: 5 * 60 * 1000,      // 5 minutes
  SHORT_TERM: 60 * 60 * 1000,    // 1 hour
  MEDIUM_TERM: 24 * 60 * 60 * 1000, // 24 hours
  LONG_TERM: 7 * 24 * 60 * 60 * 1000 // 7 days
};

// =============================================================================
// METRIC CLASSES
// =============================================================================

class Metric {
  constructor(name, type, labels = {}, options = {}) {
    this.name = name;
    this.type = type;
    this.labels = labels;
    this.timestamp = Date.now();
    this.value = options.initialValue || 0;
    this.samples = [];
    this.metadata = options.metadata || {};
  }

  setValue(value, timestamp = Date.now()) {
    this.value = value;
    this.timestamp = timestamp;
    this.addSample(value, timestamp);
  }

  increment(amount = 1, timestamp = Date.now()) {
    this.value += amount;
    this.timestamp = timestamp;
    this.addSample(this.value, timestamp);
  }

  addSample(value, timestamp = Date.now()) {
    this.samples.push({ value, timestamp });

    // Keep only recent samples
    const cutoff = timestamp - RETENTION_PERIODS.REAL_TIME;
    this.samples = this.samples.filter(sample => sample.timestamp > cutoff);
  }

  getStats() {
    if (this.samples.length === 0) {
      return { count: 0, min: 0, max: 0, avg: 0, sum: 0 };
    }

    const values = this.samples.map(s => s.value);
    const sum = values.reduce((a, b) => a + b, 0);

    return {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: sum / values.length,
      sum,
      p50: this.percentile(values, 0.5),
      p90: this.percentile(values, 0.9),
      p95: this.percentile(values, 0.95),
      p99: this.percentile(values, 0.99)
    };
  }

  percentile(values, p) {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil(sorted.length * p) - 1;
    return sorted[index] || 0;
  }
}

class Timer extends Metric {
  constructor(name, labels = {}, options = {}) {
    super(name, METRIC_TYPES.TIMER, labels, options);
    this.startTimes = new Map();
  }

  start(id = 'default') {
    this.startTimes.set(id, performance.now());
  }

  end(id = 'default') {
    const startTime = this.startTimes.get(id);
    if (startTime) {
      const duration = performance.now() - startTime;
      this.addSample(duration);
      this.startTimes.delete(id);
      return duration;
    }
    return 0;
  }

  time(fn, id = 'default') {
    this.start(id);
    try {
      const result = fn();
      if (result && typeof result.then === 'function') {
        return result.finally(() => this.end(id));
      }
      this.end(id);
      return result;
    } catch (error) {
      this.end(id);
      throw error;
    }
  }
}

// =============================================================================
// FLOW METRICS COLLECTOR CLASS
// =============================================================================

class FlowMetricsCollector extends EventEmitter {
  constructor(options = {}) {
    super();

    this.serviceName = options.serviceName || 'unknown-service';
    this.logger = options.logger || console;
    this.metricsStorage = options.storage || new Map();
    this.enableRealTimeMetrics = options.enableRealTimeMetrics !== false;
    this.enableErrorCorrelation = options.enableErrorCorrelation !== false;
    this.collectionInterval = options.collectionInterval || COLLECTION_INTERVALS.REAL_TIME;
    this.retentionPeriod = options.retentionPeriod || RETENTION_PERIODS.MEDIUM_TERM;

    // Metric registries
    this.metrics = new Map();
    this.timers = new Map();
    this.flowMetrics = new Map();
    this.errorMetrics = new Map();

    // Performance tracking
    this.performanceData = {
      flows: new Map(),
      services: new Map(),
      errors: new Map(),
      dependencies: new Map()
    };

    // Start collection intervals
    this.startCollectionIntervals();

    // Initialize default metrics
    this.initializeDefaultMetrics();
  }

  /**
   * Initialize default metrics
   */
  initializeDefaultMetrics() {
    // Flow metrics
    this.createCounter('flow_requests_total', 'Total flow requests', ['service', 'status']);
    this.createTimer('flow_duration_seconds', 'Flow duration', ['service', 'endpoint']);
    this.createGauge('flow_active_count', 'Active flows', ['service']);

    // Error metrics
    this.createCounter('flow_errors_total', 'Total flow errors', ['service', 'error_type']);
    this.createGauge('flow_error_rate', 'Flow error rate', ['service']);

    // Performance metrics
    this.createHistogram('flow_memory_usage', 'Flow memory usage', ['service']);
    this.createHistogram('flow_cpu_usage', 'Flow CPU usage', ['service']);

    // Dependency metrics
    this.createCounter('flow_dependencies_total', 'Total dependency calls', ['from_service', 'to_service']);
    this.createTimer('flow_dependency_duration', 'Dependency call duration', ['from_service', 'to_service']);
  }

  /**
   * Create counter metric
   */
  createCounter(name, description, labelNames = []) {
    const metric = new Metric(name, METRIC_TYPES.COUNTER, {}, { description, labelNames });
    this.metrics.set(name, metric);
    return metric;
  }

  /**
   * Create gauge metric
   */
  createGauge(name, description, labelNames = []) {
    const metric = new Metric(name, METRIC_TYPES.GAUGE, {}, { description, labelNames });
    this.metrics.set(name, metric);
    return metric;
  }

  /**
   * Create histogram metric
   */
  createHistogram(name, description, labelNames = []) {
    const metric = new Metric(name, METRIC_TYPES.HISTOGRAM, {}, { description, labelNames });
    this.metrics.set(name, metric);
    return metric;
  }

  /**
   * Create timer metric
   */
  createTimer(name, description, labelNames = []) {
    const timer = new Timer(name, {}, { description, labelNames });
    this.timers.set(name, timer);
    return timer;
  }

  /**
   * Collect metrics from flow context
   */
  collect(flowContext) {
    try {
      const flowId = flowContext.flowId;
      const serviceName = flowContext.serviceName;
      const metrics = flowContext.metrics;

      // Collect flow metrics
      this.collectFlowMetrics(flowContext);

      // Collect performance metrics
      this.collectPerformanceMetrics(flowContext);

      // Collect error metrics
      this.collectErrorMetrics(flowContext);

      // Collect dependency metrics
      this.collectDependencyMetrics(flowContext);

      // Store flow data
      this.storeFlowData(flowContext);

      // Emit collection event
      this.emit('metricsCollected', {
        flowId,
        serviceName,
        timestamp: Date.now(),
        metrics: this.getFlowMetricsSummary(flowId)
      });

    } catch (error) {
      this.logger.error('Error collecting flow metrics', {
        error: error.message,
        flowId: flowContext.flowId,
        serviceName: flowContext.serviceName
      });
    }
  }

  /**
   * Collect flow metrics
   */
  collectFlowMetrics(flowContext) {
    const { flowId, serviceName, metrics, serviceChain, errors } = flowContext;

    // Flow requests counter
    const status = errors.length > 0 ? 'error' : 'success';
    this.incrementCounter('flow_requests_total', 1, { service: serviceName, status });

    // Flow duration timer
    if (metrics.duration) {
      this.recordTimer('flow_duration_seconds', metrics.duration, {
        service: serviceName,
        endpoint: flowContext.metadata?.requestPath || 'unknown'
      });
    }

    // Active flows gauge (approximate)
    this.setGauge('flow_active_count', this.getActiveFlowCount(serviceName), { service: serviceName });

    // Service chain metrics
    if (serviceChain.length > 0) {
      this.recordHistogram('flow_service_chain_length', serviceChain.length, { service: serviceName });
    }
  }

  /**
   * Collect performance metrics
   */
  collectPerformanceMetrics(flowContext) {
    const { serviceName, metrics } = flowContext;

    // Memory usage
    if (metrics.finalMemoryUsage) {
      const memoryDelta = metrics.finalMemoryUsage.heapUsed - metrics.memoryUsage.heapUsed;
      this.recordHistogram('flow_memory_usage', memoryDelta, { service: serviceName });
    }

    // CPU usage
    if (metrics.finalCpuUsage) {
      const cpuDelta = metrics.finalCpuUsage.user + metrics.finalCpuUsage.system;
      this.recordHistogram('flow_cpu_usage', cpuDelta, { service: serviceName });
    }

    // Store performance data
    if (!this.performanceData.services.has(serviceName)) {
      this.performanceData.services.set(serviceName, {
        requestCount: 0,
        totalDuration: 0,
        avgDuration: 0,
        errorCount: 0,
        memoryUsage: [],
        cpuUsage: []
      });
    }

    const serviceData = this.performanceData.services.get(serviceName);
    serviceData.requestCount++;
    serviceData.totalDuration += metrics.duration || 0;
    serviceData.avgDuration = serviceData.totalDuration / serviceData.requestCount;
    serviceData.errorCount += flowContext.errors.length;
  }

  /**
   * Collect error metrics
   */
  collectErrorMetrics(flowContext) {
    const { serviceName, errors } = flowContext;

    if (errors.length === 0) return;

    // Error counters by type
    errors.forEach(error => {
      const errorType = error.code || 'unknown';
      this.incrementCounter('flow_errors_total', 1, {
        service: serviceName,
        error_type: errorType
      });

      // Store error data for correlation
      if (this.enableErrorCorrelation) {
        this.storeErrorData(flowContext, error);
      }
    });

    // Calculate error rate
    const serviceData = this.performanceData.services.get(serviceName);
    if (serviceData) {
      const errorRate = serviceData.errorCount / serviceData.requestCount;
      this.setGauge('flow_error_rate', errorRate, { service: serviceName });
    }
  }

  /**
   * Collect dependency metrics
   */
  collectDependencyMetrics(flowContext) {
    const { serviceName, dependencies } = flowContext;

    dependencies.forEach(dep => {
      // Dependency call counter
      this.incrementCounter('flow_dependencies_total', 1, {
        from_service: serviceName,
        to_service: dep.service
      });

      // Store dependency data
      const depKey = `${serviceName}->${dep.service}`;
      if (!this.performanceData.dependencies.has(depKey)) {
        this.performanceData.dependencies.set(depKey, {
          callCount: 0,
          totalDuration: 0,
          avgDuration: 0,
          errorCount: 0
        });
      }

      const depData = this.performanceData.dependencies.get(depKey);
      depData.callCount++;
    });
  }

  /**
   * Store flow data
   */
  storeFlowData(flowContext) {
    const flowData = {
      flowId: flowContext.flowId,
      serviceName: flowContext.serviceName,
      startTime: flowContext.metrics.startTime,
      endTime: flowContext.metrics.endTime,
      duration: flowContext.metrics.duration,
      serviceChain: flowContext.serviceChain,
      dependencies: Array.from(flowContext.dependencies),
      errors: flowContext.errors,
      status: flowContext.errors.length > 0 ? 'error' : 'success',
      timestamp: Date.now()
    };

    this.flowMetrics.set(flowContext.flowId, flowData);

    // Cleanup old flow data
    this.cleanupOldFlowData();
  }

  /**
   * Store error data for correlation
   */
  storeErrorData(flowContext, error) {
    const errorData = {
      flowId: flowContext.flowId,
      serviceName: flowContext.serviceName,
      error,
      serviceChain: flowContext.serviceChain,
      timestamp: Date.now(),
      correlationId: flowContext.correlationId
    };

    const errorKey = `${error.code || 'unknown'}_${Date.now()}`;
    this.errorMetrics.set(errorKey, errorData);
  }

  /**
   * Increment counter metric
   */
  incrementCounter(name, value = 1, labels = {}) {
    const metric = this.getOrCreateMetric(name, METRIC_TYPES.COUNTER, labels);
    metric.increment(value);
  }

  /**
   * Set gauge metric
   */
  setGauge(name, value, labels = {}) {
    const metric = this.getOrCreateMetric(name, METRIC_TYPES.GAUGE, labels);
    metric.setValue(value);
  }

  /**
   * Record histogram metric
   */
  recordHistogram(name, value, labels = {}) {
    const metric = this.getOrCreateMetric(name, METRIC_TYPES.HISTOGRAM, labels);
    metric.addSample(value);
  }

  /**
   * Record timer metric
   */
  recordTimer(name, duration, labels = {}) {
    const timer = this.timers.get(name) || this.createTimer(name, '', Object.keys(labels));
    timer.addSample(duration);
  }

  /**
   * Get or create metric with labels
   */
  getOrCreateMetric(name, type, labels = {}) {
    const labelKey = this.createLabelKey(labels);
    const metricKey = `${name}:${labelKey}`;

    if (!this.metrics.has(metricKey)) {
      const metric = new Metric(name, type, labels);
      this.metrics.set(metricKey, metric);
    }

    return this.metrics.get(metricKey);
  }

  /**
   * Create label key for metric identification
   */
  createLabelKey(labels) {
    return Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join(',');
  }

  /**
   * Get active flow count for service
   */
  getActiveFlowCount(serviceName) {
    let count = 0;
    const now = Date.now();
    const activeThreshold = 60000; // 1 minute

    for (const [flowId, flowData] of this.flowMetrics.entries()) {
      if (flowData.serviceName === serviceName &&
          (!flowData.endTime || now - flowData.timestamp < activeThreshold)) {
        count++;
      }
    }

    return count;
  }

  /**
   * Get flow metrics summary
   */
  getFlowMetricsSummary(flowId) {
    const flowData = this.flowMetrics.get(flowId);
    if (!flowData) return null;

    return {
      flowId,
      serviceName: flowData.serviceName,
      duration: flowData.duration,
      status: flowData.status,
      serviceChain: flowData.serviceChain,
      dependencyCount: flowData.dependencies.length,
      errorCount: flowData.errors.length,
      timestamp: flowData.timestamp
    };
  }

  /**
   * Get service metrics
   */
  getServiceMetrics(serviceName) {
    const serviceData = this.performanceData.services.get(serviceName);
    if (!serviceData) return null;

    return {
      serviceName,
      requestCount: serviceData.requestCount,
      avgDuration: serviceData.avgDuration,
      errorRate: serviceData.errorCount / serviceData.requestCount,
      ...serviceData
    };
  }

  /**
   * Get all metrics
   */
  getAllMetrics() {
    const result = {
      counters: {},
      gauges: {},
      histograms: {},
      timers: {}
    };

    for (const [key, metric] of this.metrics.entries()) {
      const category = metric.type + 's';
      if (result[category]) {
        result[category][key] = {
          name: metric.name,
          value: metric.value,
          labels: metric.labels,
          stats: metric.getStats(),
          timestamp: metric.timestamp
        };
      }
    }

    for (const [key, timer] of this.timers.entries()) {
      result.timers[key] = {
        name: timer.name,
        stats: timer.getStats(),
        timestamp: timer.timestamp
      };
    }

    return result;
  }

  /**
   * Start collection intervals
   */
  startCollectionIntervals() {
    if (this.enableRealTimeMetrics) {
      this.realTimeInterval = setInterval(() => {
        this.emit('realTimeMetrics', this.getAllMetrics());
      }, this.collectionInterval);
    }

    // Cleanup interval
    this.cleanupInterval = setInterval(() => {
      this.cleanupOldFlowData();
      this.cleanupOldErrorData();
    }, 60000); // Every minute
  }

  /**
   * Cleanup old flow data
   */
  cleanupOldFlowData() {
    const now = Date.now();
    const cutoff = now - this.retentionPeriod;

    for (const [flowId, flowData] of this.flowMetrics.entries()) {
      if (flowData.timestamp < cutoff) {
        this.flowMetrics.delete(flowId);
      }
    }
  }

  /**
   * Cleanup old error data
   */
  cleanupOldErrorData() {
    const now = Date.now();
    const cutoff = now - this.retentionPeriod;

    for (const [errorKey, errorData] of this.errorMetrics.entries()) {
      if (errorData.timestamp < cutoff) {
        this.errorMetrics.delete(errorKey);
      }
    }
  }

  /**
   * Stop collector and cleanup
   */
  stop() {
    if (this.realTimeInterval) {
      clearInterval(this.realTimeInterval);
    }

    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    this.metrics.clear();
    this.timers.clear();
    this.flowMetrics.clear();
    this.errorMetrics.clear();
    this.removeAllListeners();
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create FlowMetricsCollector instance
 */
function createFlowMetricsCollector(options = {}) {
  return new FlowMetricsCollector(options);
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  FlowMetricsCollector,
  Metric,
  Timer,
  createFlowMetricsCollector,
  METRIC_TYPES,
  COLLECTION_INTERVALS,
  RETENTION_PERIODS
};