/**
 * Trading Metrics Service
 * Comprehensive performance and trading metrics collection
 */

const EventEmitter = require('events');

class TradingMetrics extends EventEmitter {
  constructor(options = {}) {
    super();

    this.logger = options.logger || console;
    this.metricsInterval = options.metricsInterval || 5000; // 5 seconds
    this.isCollecting = false;

    // Trading performance metrics
    this.metrics = {
      // Order metrics
      totalOrders: 0,
      successfulOrders: 0,
      failedOrders: 0,
      cancelledOrders: 0,

      // Execution metrics
      averageExecutionTime: 0,
      minExecutionTime: Infinity,
      maxExecutionTime: 0,
      executionTimes: [],

      // Volume metrics
      totalVolume: 0,
      dailyVolume: 0,
      volumeByInstrument: new Map(),

      // Latency metrics
      averageLatency: 0,
      latencyHistory: [],
      latencyP95: 0,
      latencyP99: 0,

      // AI signal metrics
      aiSignalsReceived: 0,
      aiSignalsActioned: 0,
      aiSignalAccuracy: 0,

      // Flow tracking metrics
      flowsStarted: 0,
      flowsCompleted: 0,
      flowsFailed: 0,
      averageFlowDuration: 0,

      // Error metrics
      errorCount: 0,
      errorsByType: new Map(),
      lastError: null,

      // System metrics
      memoryUsage: {},
      cpuUsage: {},
      uptime: 0,

      // Trading session metrics
      sessionStartTime: Date.now(),
      lastResetTime: Date.now()
    };

    // Historical data for trend analysis
    this.historicalData = {
      daily: [],
      hourly: [],
      minutely: []
    };

    this.startCollection();
  }

  /**
   * Start metrics collection
   */
  startCollection() {
    if (this.isCollecting) {
      return;
    }

    this.isCollecting = true;
    this.collectionInterval = setInterval(() => {
      this.collectSystemMetrics();
      this.calculateDerivedMetrics();
      this.emit('metricsUpdated', this.getSnapshot());
    }, this.metricsInterval);

    this.logger.info('Trading metrics collection started', {
      service: 'trading-metrics',
      interval: `${this.metricsInterval}ms`
    });
  }

  /**
   * Stop metrics collection
   */
  stopCollection() {
    if (!this.isCollecting) {
      return;
    }

    this.isCollecting = false;
    if (this.collectionInterval) {
      clearInterval(this.collectionInterval);
    }

    this.logger.info('Trading metrics collection stopped', {
      service: 'trading-metrics'
    });
  }

  /**
   * Record order execution
   */
  recordOrderExecution(orderData) {
    const executionTime = orderData.executionTime || 0;
    const latency = orderData.latency || 0;
    const volume = orderData.volume || 0;
    const success = orderData.success !== false;

    // Update order metrics
    this.metrics.totalOrders++;
    if (success) {
      this.metrics.successfulOrders++;
    } else {
      this.metrics.failedOrders++;
    }

    // Update execution time metrics
    this.metrics.averageExecutionTime =
      (this.metrics.averageExecutionTime + executionTime) / 2;
    this.metrics.minExecutionTime = Math.min(this.metrics.minExecutionTime, executionTime);
    this.metrics.maxExecutionTime = Math.max(this.metrics.maxExecutionTime, executionTime);

    // Update latency metrics
    this.metrics.averageLatency = (this.metrics.averageLatency + latency) / 2;

    // Update volume metrics
    this.metrics.totalVolume += volume;
    this.metrics.dailyVolume += volume;

    this.logger.debug('Order execution recorded', {
      service: 'trading-metrics',
      orderId: orderData.orderId,
      executionTime: `${executionTime}ms`,
      success
    });
  }

  /**
   * Record AI signal metrics
   */
  recordAISignal(signalData) {
    this.metrics.aiSignalsReceived++;

    if (signalData.actioned) {
      this.metrics.aiSignalsActioned++;
    }

    if (signalData.accuracy !== undefined) {
      this.metrics.aiSignalAccuracy =
        (this.metrics.aiSignalAccuracy + signalData.accuracy) / 2;
    }
  }

  /**
   * Record flow tracking metrics
   */
  recordFlow(flowData) {
    this.metrics.flowsStarted++;

    if (flowData.completed) {
      if (flowData.success) {
        this.metrics.flowsCompleted++;
      } else {
        this.metrics.flowsFailed++;
      }

      if (flowData.duration) {
        this.metrics.averageFlowDuration =
          (this.metrics.averageFlowDuration + flowData.duration) / 2;
      }
    }
  }

  /**
   * Record error
   */
  recordError(errorData) {
    this.metrics.errorCount++;
    this.metrics.lastError = {
      message: errorData.message,
      type: errorData.type,
      timestamp: Date.now()
    };

    const errorType = errorData.type || 'unknown';
    const currentCount = this.metrics.errorsByType.get(errorType) || 0;
    this.metrics.errorsByType.set(errorType, currentCount + 1);
  }

  /**
   * Collect system metrics
   */
  collectSystemMetrics() {
    this.metrics.memoryUsage = process.memoryUsage();
    this.metrics.cpuUsage = process.cpuUsage();
    this.metrics.uptime = Date.now() - this.metrics.sessionStartTime;
  }

  /**
   * Calculate derived metrics
   */
  calculateDerivedMetrics() {
    // Simple implementation for now
  }

  /**
   * Get current metrics snapshot
   */
  getSnapshot() {
    return {
      timestamp: Date.now(),
      orders: {
        total: this.metrics.totalOrders,
        successful: this.metrics.successfulOrders,
        failed: this.metrics.failedOrders,
        successRate: this.metrics.totalOrders > 0 ?
          (this.metrics.successfulOrders / this.metrics.totalOrders) * 100 : 0
      },
      execution: {
        averageTime: Math.round(this.metrics.averageExecutionTime),
        minTime: this.metrics.minExecutionTime === Infinity ? 0 : this.metrics.minExecutionTime,
        maxTime: this.metrics.maxExecutionTime
      },
      latency: {
        average: Math.round(this.metrics.averageLatency)
      },
      aiSignals: {
        received: this.metrics.aiSignalsReceived,
        actioned: this.metrics.aiSignalsActioned,
        accuracy: Math.round(this.metrics.aiSignalAccuracy * 100)
      },
      flows: {
        started: this.metrics.flowsStarted,
        completed: this.metrics.flowsCompleted,
        failed: this.metrics.flowsFailed
      },
      errors: {
        count: this.metrics.errorCount,
        byType: Object.fromEntries(this.metrics.errorsByType)
      },
      system: {
        memoryUsage: this.metrics.memoryUsage,
        uptime: this.metrics.uptime
      }
    };
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary() {
    const snapshot = this.getSnapshot();

    return {
      overall: {
        status: this.getOverallStatus(),
        uptime: Math.floor(snapshot.system.uptime / 1000),
        totalOrders: snapshot.orders.total,
        successRate: snapshot.orders.successRate
      },
      performance: {
        executionTime: {
          average: snapshot.execution.averageTime,
          target: '< 10ms',
          compliance: snapshot.execution.averageTime < 10 ? 'PASSED' : 'WARNING'
        }
      }
    };
  }

  /**
   * Get overall system status
   */
  getOverallStatus() {
    return 'healthy';
  }

  /**
   * Get historical data
   */
  getHistoricalData(timeframe = 'minutely') {
    return this.historicalData[timeframe] || [];
  }

  /**
   * Health check
   */
  isHealthy() {
    return this.isCollecting;
  }
}

module.exports = TradingMetrics;