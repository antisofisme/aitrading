const EventEmitter = require('events');
const logger = require('../utils/logger');

class PerformanceMonitor extends EventEmitter {
  constructor() {
    super();
    this.isInitialized = false;
    this.isMonitoring = false;
    this.startTime = Date.now();

    // Performance metrics storage
    this.metrics = {
      // Data processing metrics
      dataProcessing: {
        totalProcessed: 0,
        successRate: 0,
        averageLatency: 0,
        ticksPerSecond: 0,
        lastTickTime: 0,
        processingErrors: 0
      },

      // Connection metrics
      connections: {
        mt5: {
          connected: false,
          uptime: 0,
          reconnectCount: 0,
          lastReconnect: 0,
          connectionLatency: 0
        },
        backend: {
          connected: false,
          uptime: 0,
          reconnectCount: 0,
          lastReconnect: 0,
          responseTime: 0
        }
      },

      // System performance
      system: {
        cpuUsage: 0,
        memoryUsage: 0,
        diskUsage: 0,
        networkLatency: 0
      },

      // Application metrics
      application: {
        uptime: 0,
        frameRate: 0,
        uiResponseTime: 0,
        cacheHitRate: 0,
        errorRate: 0
      },

      // Target compliance
      targets: {
        ticksPerSecondTarget: 50,
        maxLatencyTarget: 50, // ms
        uptimeTarget: 99.9, // percentage
        currentCompliance: 0
      }
    };

    // Historical data for trend analysis
    this.history = {
      dataPoints: [],
      maxHistoryLength: 1000,
      intervals: {
        second: [],
        minute: [],
        hour: []
      }
    };

    // Performance alerts
    this.alerts = {
      active: [],
      thresholds: {
        highLatency: 100,
        lowThroughput: 25,
        highErrorRate: 5,
        connectionLoss: 5000,
        memoryUsage: 80,
        cpuUsage: 80
      },
      cooldown: new Map() // Prevent alert spam
    };

    // Monitoring intervals
    this.intervals = {
      main: null,
      system: null,
      history: null,
      alerts: null
    };
  }

  async initialize() {
    try {
      logger.info('Initializing Performance Monitor...');

      // Initialize system monitoring
      this.initializeSystemMonitoring();

      // Setup monitoring intervals
      this.setupMonitoringIntervals();

      this.isInitialized = true;
      logger.info('Performance Monitor initialized successfully');

      this.emit('initialized');

    } catch (error) {
      logger.error('Failed to initialize Performance Monitor:', error);
      throw error;
    }
  }

  initializeSystemMonitoring() {
    // Try to load system monitoring modules
    try {
      this.os = require('os');
      this.process = require('process');
      logger.info('System monitoring enabled');
    } catch (error) {
      logger.warn('System monitoring limited:', error.message);
    }
  }

  setupMonitoringIntervals() {
    // Main metrics collection (every second)
    this.intervals.main = setInterval(() => {
      this.collectMainMetrics();
    }, 1000);

    // System metrics collection (every 5 seconds)
    this.intervals.system = setInterval(() => {
      this.collectSystemMetrics();
    }, 5000);

    // Historical data processing (every 10 seconds)
    this.intervals.history = setInterval(() => {
      this.processHistoricalData();
    }, 10000);

    // Alert checking (every 2 seconds)
    this.intervals.alerts = setInterval(() => {
      this.checkAlerts();
    }, 2000);

    logger.info('Performance monitoring intervals configured');
  }

  startMonitoring() {
    if (!this.isInitialized) {
      throw new Error('Performance Monitor not initialized');
    }

    this.isMonitoring = true;
    this.startTime = Date.now();

    logger.info('Performance monitoring started');
    this.emit('monitoringStarted');
  }

  collectMainMetrics() {
    if (!this.isMonitoring) return;

    try {
      const now = Date.now();

      // Update application uptime
      this.metrics.application.uptime = now - this.startTime;

      // Calculate current compliance with targets
      this.calculateTargetCompliance();

      // Record timestamp
      this.metrics.lastUpdate = now;

      this.emit('metricsUpdated', this.metrics);

    } catch (error) {
      logger.error('Error collecting main metrics:', error);
    }
  }

  collectSystemMetrics() {
    if (!this.isMonitoring || !this.os) return;

    try {
      // CPU usage (simplified - in real implementation you'd need more sophisticated CPU monitoring)
      const cpuLoad = this.os.loadavg()[0];
      this.metrics.system.cpuUsage = Math.min(cpuLoad * 100, 100);

      // Memory usage
      const totalMem = this.os.totalmem();
      const freeMem = this.os.freemem();
      this.metrics.system.memoryUsage = ((totalMem - freeMem) / totalMem) * 100;

      // Process memory usage
      const processMemory = process.memoryUsage();
      this.metrics.application.memoryUsed = processMemory.heapUsed / (1024 * 1024); // MB

      this.emit('systemMetricsUpdated', this.metrics.system);

    } catch (error) {
      logger.error('Error collecting system metrics:', error);
    }
  }

  calculateTargetCompliance() {
    const { dataProcessing, targets } = this.metrics;

    let compliance = 0;
    let factors = 0;

    // Ticks per second compliance
    if (dataProcessing.ticksPerSecond >= targets.ticksPerSecondTarget) {
      compliance += 25;
    } else {
      compliance += (dataProcessing.ticksPerSecond / targets.ticksPerSecondTarget) * 25;
    }
    factors++;

    // Latency compliance
    if (dataProcessing.averageLatency <= targets.maxLatencyTarget) {
      compliance += 25;
    } else if (dataProcessing.averageLatency <= targets.maxLatencyTarget * 2) {
      compliance += 25 * (1 - ((dataProcessing.averageLatency - targets.maxLatencyTarget) / targets.maxLatencyTarget));
    }
    factors++;

    // Connection compliance
    const mt5Connected = this.metrics.connections.mt5.connected ? 25 : 0;
    const backendConnected = this.metrics.connections.backend.connected ? 25 : 0;
    compliance += mt5Connected + backendConnected;
    factors += 2;

    targets.currentCompliance = factors > 0 ? compliance / factors : 0;
  }

  processHistoricalData() {
    if (!this.isMonitoring) return;

    try {
      const now = Date.now();
      const currentMetrics = {
        timestamp: now,
        ticksPerSecond: this.metrics.dataProcessing.ticksPerSecond,
        averageLatency: this.metrics.dataProcessing.averageLatency,
        cpuUsage: this.metrics.system.cpuUsage,
        memoryUsage: this.metrics.system.memoryUsage,
        compliance: this.metrics.targets.currentCompliance
      };

      // Add to main history
      this.history.dataPoints.push(currentMetrics);

      // Limit history size
      if (this.history.dataPoints.length > this.history.maxHistoryLength) {
        this.history.dataPoints = this.history.dataPoints.slice(-this.history.maxHistoryLength);
      }

      // Process intervals
      this.processIntervalData(currentMetrics);

    } catch (error) {
      logger.error('Error processing historical data:', error);
    }
  }

  processIntervalData(metrics) {
    const { intervals } = this.history;
    const now = metrics.timestamp;

    // Second interval (keep last 60 seconds)
    intervals.second.push(metrics);
    if (intervals.second.length > 60) {
      intervals.second = intervals.second.slice(-60);
    }

    // Minute interval (aggregate by minute, keep last 60 minutes)
    const minuteKey = Math.floor(now / 60000) * 60000;
    let minuteData = intervals.minute.find(d => d.timestamp === minuteKey);

    if (!minuteData) {
      minuteData = {
        timestamp: minuteKey,
        avgTicksPerSecond: 0,
        avgLatency: 0,
        avgCpuUsage: 0,
        avgMemoryUsage: 0,
        samples: 0
      };
      intervals.minute.push(minuteData);
    }

    // Update minute aggregate
    minuteData.samples++;
    minuteData.avgTicksPerSecond = ((minuteData.avgTicksPerSecond * (minuteData.samples - 1)) + metrics.ticksPerSecond) / minuteData.samples;
    minuteData.avgLatency = ((minuteData.avgLatency * (minuteData.samples - 1)) + metrics.averageLatency) / minuteData.samples;
    minuteData.avgCpuUsage = ((minuteData.avgCpuUsage * (minuteData.samples - 1)) + metrics.cpuUsage) / minuteData.samples;
    minuteData.avgMemoryUsage = ((minuteData.avgMemoryUsage * (minuteData.samples - 1)) + metrics.memoryUsage) / minuteData.samples;

    // Limit minute history
    if (intervals.minute.length > 60) {
      intervals.minute = intervals.minute.slice(-60);
    }

    // Hour interval (aggregate by hour, keep last 24 hours)
    const hourKey = Math.floor(now / 3600000) * 3600000;
    let hourData = intervals.hour.find(d => d.timestamp === hourKey);

    if (!hourData) {
      hourData = {
        timestamp: hourKey,
        avgTicksPerSecond: 0,
        avgLatency: 0,
        avgCpuUsage: 0,
        avgMemoryUsage: 0,
        samples: 0
      };
      intervals.hour.push(hourData);
    }

    // Update hour aggregate
    hourData.samples++;
    hourData.avgTicksPerSecond = ((hourData.avgTicksPerSecond * (hourData.samples - 1)) + metrics.ticksPerSecond) / hourData.samples;
    hourData.avgLatency = ((hourData.avgLatency * (hourData.samples - 1)) + metrics.averageLatency) / hourData.samples;
    hourData.avgCpuUsage = ((hourData.avgCpuUsage * (hourData.samples - 1)) + metrics.cpuUsage) / hourData.samples;
    hourData.avgMemoryUsage = ((hourData.avgMemoryUsage * (hourData.samples - 1)) + metrics.memoryUsage) / hourData.samples;

    // Limit hour history
    if (intervals.hour.length > 24) {
      intervals.hour = intervals.hour.slice(-24);
    }
  }

  checkAlerts() {
    if (!this.isMonitoring) return;

    const now = Date.now();
    const newAlerts = [];

    // Check each threshold
    Object.keys(this.alerts.thresholds).forEach(alertType => {
      const threshold = this.alerts.thresholds[alertType];
      const cooldownKey = alertType;

      // Check if alert is in cooldown
      if (this.alerts.cooldown.has(cooldownKey) &&
          now - this.alerts.cooldown.get(cooldownKey) < 60000) {
        return; // Skip if in 1-minute cooldown
      }

      let shouldAlert = false;
      let currentValue = 0;
      let message = '';

      switch (alertType) {
        case 'highLatency':
          currentValue = this.metrics.dataProcessing.averageLatency;
          shouldAlert = currentValue > threshold;
          message = `High latency detected: ${currentValue.toFixed(2)}ms (threshold: ${threshold}ms)`;
          break;

        case 'lowThroughput':
          currentValue = this.metrics.dataProcessing.ticksPerSecond;
          shouldAlert = currentValue < threshold;
          message = `Low throughput detected: ${currentValue.toFixed(2)} TPS (threshold: ${threshold} TPS)`;
          break;

        case 'highErrorRate':
          currentValue = this.metrics.application.errorRate;
          shouldAlert = currentValue > threshold;
          message = `High error rate detected: ${currentValue.toFixed(2)}% (threshold: ${threshold}%)`;
          break;

        case 'connectionLoss':
          const lastTick = now - this.metrics.dataProcessing.lastTickTime;
          currentValue = lastTick;
          shouldAlert = lastTick > threshold && this.metrics.dataProcessing.lastTickTime > 0;
          message = `Connection loss detected: no ticks for ${(lastTick/1000).toFixed(1)}s`;
          break;

        case 'memoryUsage':
          currentValue = this.metrics.system.memoryUsage;
          shouldAlert = currentValue > threshold;
          message = `High memory usage: ${currentValue.toFixed(1)}% (threshold: ${threshold}%)`;
          break;

        case 'cpuUsage':
          currentValue = this.metrics.system.cpuUsage;
          shouldAlert = currentValue > threshold;
          message = `High CPU usage: ${currentValue.toFixed(1)}% (threshold: ${threshold}%)`;
          break;
      }

      if (shouldAlert) {
        const alert = {
          type: alertType,
          message,
          currentValue,
          threshold,
          timestamp: now,
          severity: this.getAlertSeverity(alertType, currentValue, threshold)
        };

        newAlerts.push(alert);
        this.alerts.cooldown.set(cooldownKey, now);

        logger.warn(`Performance alert: ${message}`);
      }
    });

    // Add new alerts
    newAlerts.forEach(alert => {
      this.alerts.active.push(alert);
      this.emit('alert', alert);
    });

    // Clean up old alerts (older than 5 minutes)
    this.alerts.active = this.alerts.active.filter(alert =>
      now - alert.timestamp < 5 * 60 * 1000
    );
  }

  getAlertSeverity(alertType, currentValue, threshold) {
    const criticalTypes = ['connectionLoss', 'highErrorRate'];

    if (criticalTypes.includes(alertType)) {
      return 'critical';
    }

    const ratio = alertType.includes('low') ?
      threshold / currentValue :
      currentValue / threshold;

    if (ratio >= 2) return 'critical';
    if (ratio >= 1.5) return 'high';
    return 'medium';
  }

  // Public interface methods for recording metrics
  recordDataProcessing(metrics) {
    this.metrics.dataProcessing.totalProcessed++;
    this.metrics.dataProcessing.lastTickTime = Date.now();

    if (metrics.latency !== undefined) {
      this.updateAverageLatency(metrics.latency);
    }

    if (metrics.error) {
      this.metrics.dataProcessing.processingErrors++;
    }

    // Calculate TPS
    this.calculateTicksPerSecond();
  }

  updateAverageLatency(latency) {
    const current = this.metrics.dataProcessing.averageLatency;
    if (current === 0) {
      this.metrics.dataProcessing.averageLatency = latency;
    } else {
      // Exponential moving average
      this.metrics.dataProcessing.averageLatency = (current * 0.9) + (latency * 0.1);
    }
  }

  calculateTicksPerSecond() {
    const now = Date.now();
    const timeWindow = 10000; // 10 seconds

    // Count ticks in the last 10 seconds
    const recentHistory = this.history.dataPoints.filter(point =>
      now - point.timestamp <= timeWindow
    );

    if (recentHistory.length > 0) {
      const tickCount = recentHistory.length;
      const timeSpan = (now - recentHistory[0].timestamp) / 1000; // seconds
      this.metrics.dataProcessing.ticksPerSecond = timeSpan > 0 ? tickCount / timeSpan : 0;
    }
  }

  recordConnectionStatus(service, connected, latency = 0) {
    const connection = this.metrics.connections[service];
    if (!connection) return;

    const wasConnected = connection.connected;
    connection.connected = connected;

    if (connected) {
      if (!wasConnected) {
        // Just reconnected
        connection.reconnectCount++;
        connection.lastReconnect = Date.now();
      }

      if (latency > 0) {
        connection.connectionLatency = latency;
      }
    } else {
      connection.uptime = 0;
    }
  }

  recordDataMetrics(metrics) {
    if (metrics.type === 'tick') {
      this.recordDataProcessing({
        latency: metrics.latency,
        error: metrics.error
      });
    }
  }

  // Public getters
  getMetrics() {
    return {
      ...this.metrics,
      isMonitoring: this.isMonitoring,
      alerts: {
        active: this.alerts.active.length,
        recent: this.alerts.active.slice(-5)
      }
    };
  }

  getDetailedMetrics() {
    return {
      current: this.metrics,
      history: {
        recent: this.history.dataPoints.slice(-60), // Last minute
        minute: this.history.intervals.minute.slice(-60), // Last hour
        hour: this.history.intervals.hour.slice(-24) // Last day
      },
      alerts: this.alerts.active,
      performance: {
        targetCompliance: this.metrics.targets.currentCompliance,
        recommendations: this.getPerformanceRecommendations()
      }
    };
  }

  getPerformanceRecommendations() {
    const recommendations = [];
    const { dataProcessing, system, targets } = this.metrics;

    if (dataProcessing.ticksPerSecond < targets.ticksPerSecondTarget * 0.8) {
      recommendations.push({
        type: 'performance',
        message: 'Consider optimizing data processing pipeline to improve throughput',
        priority: 'high'
      });
    }

    if (dataProcessing.averageLatency > targets.maxLatencyTarget) {
      recommendations.push({
        type: 'latency',
        message: 'High latency detected. Check network connection and reduce processing complexity',
        priority: 'high'
      });
    }

    if (system.memoryUsage > 70) {
      recommendations.push({
        type: 'memory',
        message: 'High memory usage. Consider increasing cache cleanup frequency',
        priority: 'medium'
      });
    }

    if (system.cpuUsage > 70) {
      recommendations.push({
        type: 'cpu',
        message: 'High CPU usage. Consider reducing monitoring frequency or optimizing algorithms',
        priority: 'medium'
      });
    }

    return recommendations;
  }

  // Cleanup
  async stop() {
    logger.info('Stopping Performance Monitor...');

    this.isMonitoring = false;

    // Clear all intervals
    Object.keys(this.intervals).forEach(key => {
      if (this.intervals[key]) {
        clearInterval(this.intervals[key]);
        this.intervals[key] = null;
      }
    });

    logger.info('Performance Monitor stopped');
    this.emit('stopped');
  }
}

module.exports = PerformanceMonitor;