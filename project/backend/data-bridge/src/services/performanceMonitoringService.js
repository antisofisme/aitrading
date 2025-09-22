/**
 * Level 3 Performance Monitoring Service
 * Comprehensive performance tracking for Level 3 targets:
 * - 50+ ticks/second processing capacity
 * - Sub-10ms data processing latency
 * - 99.9% data accuracy and completeness
 */

const EventEmitter = require('events');
const logger = require('../utils/logger');

class PerformanceMonitoringService extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      metricsCollectionInterval: 5000, // 5 seconds
      performanceWindowSize: 60, // 60 data points (5 minutes at 5-second intervals)
      alertThresholds: {
        ticksPerSecond: 50, // Level 3 target
        maxLatency: 10, // Sub-10ms requirement
        minAccuracy: 99.9, // 99.9% accuracy target
        minUptime: 99.9 // 99.9% uptime target
      },
      historicalDataRetention: 1440, // 24 hours of 1-minute intervals
      enableAlerting: true,
      enableTrendAnalysis: true,
      ...config
    };

    this.metrics = {
      current: this.initializeCurrentMetrics(),
      historical: [],
      alerts: [],
      trends: {}
    };

    this.performanceWindow = [];
    this.startTime = Date.now();
    this.lastMetricsUpdate = Date.now();

    this.setupMetricsCollection();
  }

  initializeCurrentMetrics() {
    return {
      timestamp: new Date().toISOString(),
      performance: {
        ticksPerSecond: 0,
        averageLatency: 0,
        maxLatency: 0,
        minLatency: Infinity,
        dataAccuracy: 100,
        uptime: 0,
        systemLoad: 0
      },
      throughput: {
        totalTicks: 0,
        validTicks: 0,
        invalidTicks: 0,
        processedBytes: 0,
        connectionsActive: 0
      },
      system: {
        memoryUsage: process.memoryUsage(),
        cpuUsage: 0,
        networkLatency: 0,
        diskIO: 0
      },
      dataFlow: {
        sourcesActive: 0,
        subscriptionsActive: 0,
        bufferUtilization: 0,
        failoverEvents: 0
      }
    };
  }

  setupMetricsCollection() {
    // Collect metrics at regular intervals
    this.metricsInterval = setInterval(() => {
      this.collectMetrics();
    }, this.config.metricsCollectionInterval);

    // Perform trend analysis less frequently
    this.trendAnalysisInterval = setInterval(() => {
      if (this.config.enableTrendAnalysis) {
        this.performTrendAnalysis();
      }
    }, 60000); // Every minute

    logger.info('Performance monitoring service initialized', {
      interval: this.config.metricsCollectionInterval,
      targets: this.config.alertThresholds
    });
  }

  /**
   * Record a processing latency measurement
   * @param {number} latency - Processing latency in milliseconds
   * @param {string} operation - Operation type
   */
  recordLatency(latency, operation = 'data_processing') {
    const current = this.metrics.current.performance;

    // Update latency statistics
    current.averageLatency = this.updateMovingAverage(
      current.averageLatency,
      latency,
      100 // Sample size for moving average
    );

    current.maxLatency = Math.max(current.maxLatency, latency);
    current.minLatency = Math.min(current.minLatency, latency);

    // Check latency threshold
    if (latency > this.config.alertThresholds.maxLatency) {
      this.generateAlert('HIGH_LATENCY', {
        measured: latency,
        threshold: this.config.alertThresholds.maxLatency,
        operation
      });
    }

    this.emit('latencyRecorded', { latency, operation, timestamp: Date.now() });
  }

  /**
   * Record tick processing event
   * @param {number} tickCount - Number of ticks processed
   * @param {boolean} isValid - Whether the tick was valid
   */
  recordTickProcessing(tickCount = 1, isValid = true) {
    const throughput = this.metrics.current.throughput;

    throughput.totalTicks += tickCount;
    if (isValid) {
      throughput.validTicks += tickCount;
    } else {
      throughput.invalidTicks += tickCount;
    }

    // Update data accuracy
    this.metrics.current.performance.dataAccuracy =
      (throughput.validTicks / Math.max(throughput.totalTicks, 1)) * 100;

    this.emit('tickProcessed', { tickCount, isValid, timestamp: Date.now() });
  }

  /**
   * Record data throughput
   * @param {number} bytes - Bytes processed
   */
  recordDataThroughput(bytes) {
    this.metrics.current.throughput.processedBytes += bytes;
    this.emit('dataThroughput', { bytes, timestamp: Date.now() });
  }

  /**
   * Update connection count
   * @param {number} activeConnections - Current active connections
   */
  updateConnectionCount(activeConnections) {
    this.metrics.current.throughput.connectionsActive = activeConnections;
    this.emit('connectionsUpdated', { activeConnections, timestamp: Date.now() });
  }

  /**
   * Record system performance metrics
   * @param {Object} systemMetrics - System performance data
   */
  recordSystemMetrics(systemMetrics) {
    Object.assign(this.metrics.current.system, systemMetrics);
    this.emit('systemMetricsUpdated', { systemMetrics, timestamp: Date.now() });
  }

  /**
   * Record data flow metrics
   * @param {Object} dataFlowMetrics - Data flow performance data
   */
  recordDataFlowMetrics(dataFlowMetrics) {
    Object.assign(this.metrics.current.dataFlow, dataFlowMetrics);
    this.emit('dataFlowUpdated', { dataFlowMetrics, timestamp: Date.now() });
  }

  collectMetrics() {
    const now = Date.now();
    const timeDelta = now - this.lastMetricsUpdate;

    // Calculate ticks per second
    const windowStart = Math.max(0, this.performanceWindow.length - 12); // Last minute
    const recentMetrics = this.performanceWindow.slice(windowStart);

    if (recentMetrics.length > 0) {
      const totalTicks = recentMetrics.reduce((sum, m) => sum + m.throughput.totalTicks, 0);
      const timeSpan = recentMetrics.length * (this.config.metricsCollectionInterval / 1000);
      this.metrics.current.performance.ticksPerSecond = totalTicks / timeSpan;
    }

    // Update uptime
    this.metrics.current.performance.uptime = ((now - this.startTime) / 1000) / 3600; // Hours

    // Update system load (simplified)
    this.metrics.current.performance.systemLoad = this.calculateSystemLoad();

    // Store current metrics snapshot
    const metricsSnapshot = JSON.parse(JSON.stringify(this.metrics.current));
    metricsSnapshot.timestamp = new Date().toISOString();

    this.performanceWindow.push(metricsSnapshot);

    // Maintain window size
    if (this.performanceWindow.length > this.config.performanceWindowSize) {
      this.performanceWindow.shift();
    }

    // Store in historical data (every minute)
    if (this.performanceWindow.length % 12 === 0) { // 12 * 5 seconds = 1 minute
      this.storeHistoricalMetrics(metricsSnapshot);
    }

    // Check performance targets
    this.checkPerformanceTargets();

    this.lastMetricsUpdate = now;
    this.emit('metricsCollected', metricsSnapshot);
  }

  calculateSystemLoad() {
    // Simplified system load calculation
    const memUsage = process.memoryUsage();
    const totalMem = memUsage.heapTotal + memUsage.external;
    const usedMem = memUsage.heapUsed;

    return (usedMem / totalMem) * 100;
  }

  storeHistoricalMetrics(metricsSnapshot) {
    this.metrics.historical.push(metricsSnapshot);

    // Maintain historical data retention
    if (this.metrics.historical.length > this.config.historicalDataRetention) {
      this.metrics.historical.shift();
    }
  }

  checkPerformanceTargets() {
    const current = this.metrics.current.performance;
    const thresholds = this.config.alertThresholds;

    // Check ticks per second target
    if (current.ticksPerSecond < thresholds.ticksPerSecond) {
      this.generateAlert('LOW_THROUGHPUT', {
        measured: current.ticksPerSecond,
        threshold: thresholds.ticksPerSecond
      });
    }

    // Check data accuracy target
    if (current.dataAccuracy < thresholds.minAccuracy) {
      this.generateAlert('LOW_DATA_ACCURACY', {
        measured: current.dataAccuracy,
        threshold: thresholds.minAccuracy
      });
    }

    // Check average latency
    if (current.averageLatency > thresholds.maxLatency) {
      this.generateAlert('HIGH_AVERAGE_LATENCY', {
        measured: current.averageLatency,
        threshold: thresholds.maxLatency
      });
    }

    // Emit performance status
    const allTargetsMet =
      current.ticksPerSecond >= thresholds.ticksPerSecond &&
      current.dataAccuracy >= thresholds.minAccuracy &&
      current.averageLatency <= thresholds.maxLatency;

    this.emit('performanceTargetsChecked', {
      targetsMetStatus: {
        throughput: current.ticksPerSecond >= thresholds.ticksPerSecond,
        accuracy: current.dataAccuracy >= thresholds.minAccuracy,
        latency: current.averageLatency <= thresholds.maxLatency
      },
      allTargetsMet,
      current,
      thresholds
    });
  }

  generateAlert(type, details) {
    if (!this.config.enableAlerting) return;

    const alert = {
      id: this.generateAlertId(),
      type,
      severity: this.getAlertSeverity(type),
      message: this.getAlertMessage(type, details),
      details,
      timestamp: new Date().toISOString(),
      acknowledged: false
    };

    this.metrics.alerts.push(alert);

    // Maintain alert history (keep last 100 alerts)
    if (this.metrics.alerts.length > 100) {
      this.metrics.alerts.shift();
    }

    logger.warn(`Performance alert generated: ${alert.type}`, alert);
    this.emit('alertGenerated', alert);

    return alert;
  }

  getAlertSeverity(type) {
    const severityMap = {
      'HIGH_LATENCY': 'warning',
      'LOW_THROUGHPUT': 'critical',
      'LOW_DATA_ACCURACY': 'critical',
      'HIGH_AVERAGE_LATENCY': 'warning',
      'SYSTEM_OVERLOAD': 'critical',
      'DATA_FEED_DISCONNECTED': 'critical'
    };

    return severityMap[type] || 'info';
  }

  getAlertMessage(type, details) {
    const messageMap = {
      'HIGH_LATENCY': `High processing latency detected: ${details.measured.toFixed(2)}ms (threshold: ${details.threshold}ms)`,
      'LOW_THROUGHPUT': `Low throughput detected: ${details.measured.toFixed(2)} TPS (target: ${details.threshold} TPS)`,
      'LOW_DATA_ACCURACY': `Data accuracy below threshold: ${details.measured.toFixed(2)}% (target: ${details.threshold}%)`,
      'HIGH_AVERAGE_LATENCY': `Average latency exceeds threshold: ${details.measured.toFixed(2)}ms (threshold: ${details.threshold}ms)`,
      'SYSTEM_OVERLOAD': 'System resources are overloaded',
      'DATA_FEED_DISCONNECTED': 'Data feed connection lost'
    };

    return messageMap[type] || `Performance alert: ${type}`;
  }

  performTrendAnalysis() {
    if (this.metrics.historical.length < 10) {
      return; // Need more data for trend analysis
    }

    const recent = this.metrics.historical.slice(-60); // Last hour
    const trends = {};

    // Analyze throughput trend
    const throughputValues = recent.map(m => m.performance.ticksPerSecond);
    trends.throughput = this.calculateTrend(throughputValues);

    // Analyze latency trend
    const latencyValues = recent.map(m => m.performance.averageLatency);
    trends.latency = this.calculateTrend(latencyValues);

    // Analyze accuracy trend
    const accuracyValues = recent.map(m => m.performance.dataAccuracy);
    trends.accuracy = this.calculateTrend(accuracyValues);

    // Analyze system load trend
    const systemLoadValues = recent.map(m => m.performance.systemLoad);
    trends.systemLoad = this.calculateTrend(systemLoadValues);

    this.metrics.trends = {
      ...trends,
      lastAnalysis: new Date().toISOString()
    };

    // Generate trend-based alerts
    this.checkTrendAlerts(trends);

    this.emit('trendAnalysisCompleted', this.metrics.trends);
  }

  calculateTrend(values) {
    if (values.length < 2) return { direction: 'stable', slope: 0, correlation: 0 };

    const n = values.length;
    const indices = Array.from({ length: n }, (_, i) => i);

    // Calculate linear regression
    const sumX = indices.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = indices.reduce((sum, x, i) => sum + (x * values[i]), 0);
    const sumXX = indices.reduce((sum, x) => sum + (x * x), 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);

    // Calculate correlation coefficient
    const meanX = sumX / n;
    const meanY = sumY / n;

    const numerator = indices.reduce((sum, x, i) => sum + ((x - meanX) * (values[i] - meanY)), 0);
    const denomX = Math.sqrt(indices.reduce((sum, x) => sum + Math.pow(x - meanX, 2), 0));
    const denomY = Math.sqrt(values.reduce((sum, y) => sum + Math.pow(y - meanY, 2), 0));

    const correlation = denomX && denomY ? numerator / (denomX * denomY) : 0;

    let direction = 'stable';
    if (Math.abs(slope) > 0.1) {
      direction = slope > 0 ? 'increasing' : 'decreasing';
    }

    return {
      direction,
      slope: Number(slope.toFixed(4)),
      correlation: Number(correlation.toFixed(4)),
      strength: Math.abs(correlation) > 0.7 ? 'strong' : Math.abs(correlation) > 0.3 ? 'moderate' : 'weak'
    };
  }

  checkTrendAlerts(trends) {
    // Alert on concerning trends
    if (trends.throughput.direction === 'decreasing' && trends.throughput.strength === 'strong') {
      this.generateAlert('THROUGHPUT_DECLINING', {
        trend: trends.throughput,
        recommendation: 'Investigate data source performance'
      });
    }

    if (trends.latency.direction === 'increasing' && trends.latency.strength === 'strong') {
      this.generateAlert('LATENCY_INCREASING', {
        trend: trends.latency,
        recommendation: 'Check system resources and optimize processing'
      });
    }
  }

  updateMovingAverage(currentAvg, newValue, sampleSize) {
    // Simple exponential moving average
    const alpha = 2 / (sampleSize + 1);
    return (newValue * alpha) + (currentAvg * (1 - alpha));
  }

  generateAlertId() {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current performance report
   * @returns {Object} Performance report
   */
  getPerformanceReport() {
    const report = {
      summary: {
        status: this.getOverallStatus(),
        targetsMetPercentage: this.calculateTargetsMetPercentage(),
        alertsCount: this.metrics.alerts.filter(a => !a.acknowledged).length
      },
      current: this.metrics.current,
      trends: this.metrics.trends,
      recentAlerts: this.metrics.alerts.slice(-10),
      recommendations: this.generateRecommendations(),
      timestamp: new Date().toISOString()
    };

    return report;
  }

  getOverallStatus() {
    const current = this.metrics.current.performance;
    const thresholds = this.config.alertThresholds;

    const targetsMetCount = [
      current.ticksPerSecond >= thresholds.ticksPerSecond,
      current.dataAccuracy >= thresholds.minAccuracy,
      current.averageLatency <= thresholds.maxLatency
    ].filter(Boolean).length;

    if (targetsMetCount === 3) return 'excellent';
    if (targetsMetCount === 2) return 'good';
    if (targetsMetCount === 1) return 'warning';
    return 'critical';
  }

  calculateTargetsMetPercentage() {
    const current = this.metrics.current.performance;
    const thresholds = this.config.alertThresholds;

    const targets = [
      current.ticksPerSecond >= thresholds.ticksPerSecond,
      current.dataAccuracy >= thresholds.minAccuracy,
      current.averageLatency <= thresholds.maxLatency
    ];

    return (targets.filter(Boolean).length / targets.length) * 100;
  }

  generateRecommendations() {
    const recommendations = [];
    const current = this.metrics.current.performance;
    const thresholds = this.config.alertThresholds;

    if (current.ticksPerSecond < thresholds.ticksPerSecond) {
      recommendations.push({
        type: 'throughput',
        priority: 'high',
        message: 'Optimize data processing pipeline to increase throughput',
        actions: ['Enable parallel processing', 'Optimize data source connections', 'Review buffer sizes']
      });
    }

    if (current.averageLatency > thresholds.maxLatency) {
      recommendations.push({
        type: 'latency',
        priority: 'high',
        message: 'Reduce processing latency to meet sub-10ms target',
        actions: ['Optimize data validation logic', 'Use more efficient data structures', 'Consider caching frequently used data']
      });
    }

    if (current.dataAccuracy < thresholds.minAccuracy) {
      recommendations.push({
        type: 'accuracy',
        priority: 'critical',
        message: 'Improve data quality to meet 99.9% accuracy target',
        actions: ['Review data validation rules', 'Implement better anomaly detection', 'Check data source reliability']
      });
    }

    return recommendations;
  }

  // Acknowledge an alert
  acknowledgeAlert(alertId) {
    const alert = this.metrics.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      alert.acknowledgedAt = new Date().toISOString();
      this.emit('alertAcknowledged', alert);
    }
  }

  // Reset metrics (for testing or restart)
  resetMetrics() {
    this.metrics.current = this.initializeCurrentMetrics();
    this.metrics.alerts = [];
    this.performanceWindow = [];
    this.startTime = Date.now();
    this.lastMetricsUpdate = Date.now();
  }

  // Cleanup
  shutdown() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }
    if (this.trendAnalysisInterval) {
      clearInterval(this.trendAnalysisInterval);
    }

    logger.info('Performance monitoring service shutdown complete');
    this.emit('serviceShutdown');
  }
}

module.exports = PerformanceMonitoringService;