/**
 * Database Health Monitor
 * Centralized health monitoring for all database instances
 */

const EventEmitter = require('events');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/health-monitor.log' })
  ]
});

class HealthMonitor extends EventEmitter {
  constructor(databaseFactory) {
    super();
    this.databaseFactory = databaseFactory;
    this.healthChecks = new Map();
    this.monitoringInterval = null;
    this.checkInterval = 30000; // 30 seconds
    this.alertThresholds = {
      responseTime: 5000, // 5 seconds
      consecutiveFailures: 3,
      memoryUsage: 0.9 // 90%
    };
    this.healthHistory = new Map();
    this.maxHistorySize = 100;
    this.isMonitoring = false;
  }

  /**
   * Start health monitoring
   * @param {number} intervalMs - Monitoring interval in milliseconds
   */
  startMonitoring(intervalMs = this.checkInterval) {
    if (this.isMonitoring) {
      logger.warn('Health monitoring is already running');
      return;
    }

    this.checkInterval = intervalMs;
    this.isMonitoring = true;

    logger.info('Starting database health monitoring', { interval: intervalMs });

    // Perform initial health check
    this.performHealthChecks();

    // Set up periodic monitoring
    this.monitoringInterval = setInterval(() => {
      this.performHealthChecks();
    }, intervalMs);

    this.emit('monitoring_started', { interval: intervalMs });
  }

  /**
   * Stop health monitoring
   */
  stopMonitoring() {
    if (!this.isMonitoring) {
      logger.warn('Health monitoring is not running');
      return;
    }

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    this.isMonitoring = false;
    logger.info('Database health monitoring stopped');
    this.emit('monitoring_stopped');
  }

  /**
   * Perform health checks on all databases
   */
  async performHealthChecks() {
    const databases = this.databaseFactory.getAllDatabases();
    const checkPromises = [];

    databases.forEach((database, type) => {
      checkPromises.push(this.checkDatabaseHealth(type, database));
    });

    try {
      const results = await Promise.allSettled(checkPromises);
      const summary = this.processHealthCheckResults(results);

      logger.debug('Health check cycle completed', {
        total: results.length,
        healthy: summary.healthy,
        unhealthy: summary.unhealthy,
        degraded: summary.degraded
      });

      this.emit('health_check_completed', summary);
    } catch (error) {
      logger.error('Error performing health checks:', error);
      this.emit('health_check_error', error);
    }
  }

  /**
   * Check health of a specific database
   * @param {string} type - Database type
   * @param {IDatabaseManager} database - Database instance
   */
  async checkDatabaseHealth(type, database) {
    const startTime = Date.now();

    try {
      const healthResult = await database.healthCheck();
      const responseTime = Date.now() - startTime;

      const healthData = {
        type,
        status: healthResult.status,
        responseTime,
        timestamp: new Date().toISOString(),
        details: healthResult.details || {},
        consecutiveFailures: 0
      };

      // Update consecutive failures counter
      const previousHealth = this.healthChecks.get(type);
      if (previousHealth && healthResult.status !== 'healthy') {
        healthData.consecutiveFailures = (previousHealth.consecutiveFailures || 0) + 1;
      }

      this.updateHealthStatus(type, healthData);
      this.checkAlertConditions(type, healthData);

      return { type, status: 'fulfilled', value: healthData };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      const healthData = {
        type,
        status: 'error',
        responseTime,
        timestamp: new Date().toISOString(),
        error: error.message,
        consecutiveFailures: (this.healthChecks.get(type)?.consecutiveFailures || 0) + 1
      };

      this.updateHealthStatus(type, healthData);
      this.checkAlertConditions(type, healthData);

      logger.error(`Health check failed for ${type}:`, error);
      return { type, status: 'rejected', reason: error };
    }
  }

  /**
   * Update health status for a database
   * @param {string} type - Database type
   * @param {Object} healthData - Health check data
   */
  updateHealthStatus(type, healthData) {
    this.healthChecks.set(type, healthData);

    // Update health history
    if (!this.healthHistory.has(type)) {
      this.healthHistory.set(type, []);
    }

    const history = this.healthHistory.get(type);
    history.push(healthData);

    // Limit history size
    if (history.length > this.maxHistorySize) {
      history.shift();
    }

    this.emit('database_health_updated', { type, health: healthData });
  }

  /**
   * Check if alert conditions are met
   * @param {string} type - Database type
   * @param {Object} healthData - Health check data
   */
  checkAlertConditions(type, healthData) {
    const alerts = [];

    // High response time alert
    if (healthData.responseTime > this.alertThresholds.responseTime) {
      alerts.push({
        type: 'high_response_time',
        database: type,
        value: healthData.responseTime,
        threshold: this.alertThresholds.responseTime,
        severity: 'warning'
      });
    }

    // Consecutive failures alert
    if (healthData.consecutiveFailures >= this.alertThresholds.consecutiveFailures) {
      alerts.push({
        type: 'consecutive_failures',
        database: type,
        value: healthData.consecutiveFailures,
        threshold: this.alertThresholds.consecutiveFailures,
        severity: 'critical'
      });
    }

    // Database-specific alerts
    if (healthData.status === 'unhealthy' || healthData.status === 'error') {
      alerts.push({
        type: 'database_unhealthy',
        database: type,
        status: healthData.status,
        error: healthData.error,
        severity: 'critical'
      });
    }

    // Memory usage alert (for applicable databases)
    if (healthData.details && healthData.details.memoryUsage) {
      const memUsage = parseFloat(healthData.details.memoryUsage);
      if (memUsage > this.alertThresholds.memoryUsage) {
        alerts.push({
          type: 'high_memory_usage',
          database: type,
          value: memUsage,
          threshold: this.alertThresholds.memoryUsage,
          severity: 'warning'
        });
      }
    }

    // Emit alerts
    alerts.forEach(alert => {
      logger.warn('Database alert triggered:', alert);
      this.emit('database_alert', alert);
    });
  }

  /**
   * Process health check results
   * @param {Array} results - Health check results
   */
  processHealthCheckResults(results) {
    const summary = {
      timestamp: new Date().toISOString(),
      total: results.length,
      healthy: 0,
      unhealthy: 0,
      degraded: 0,
      error: 0,
      databases: {}
    };

    results.forEach(result => {
      if (result.status === 'fulfilled') {
        const health = result.value;
        summary.databases[health.type] = health;

        switch (health.status) {
          case 'healthy':
            summary.healthy++;
            break;
          case 'unhealthy':
            summary.unhealthy++;
            break;
          case 'degraded':
            summary.degraded++;
            break;
          default:
            summary.error++;
        }
      } else {
        summary.error++;
        summary.databases[result.type] = {
          status: 'error',
          error: result.reason.message
        };
      }
    });

    return summary;
  }

  /**
   * Get current health status
   * @param {string} type - Database type (optional)
   */
  getHealthStatus(type = null) {
    if (type) {
      return this.healthChecks.get(type) || null;
    }

    const status = {
      monitoring: this.isMonitoring,
      checkInterval: this.checkInterval,
      lastUpdate: new Date().toISOString(),
      databases: {}
    };

    this.healthChecks.forEach((health, dbType) => {
      status.databases[dbType] = health;
    });

    return status;
  }

  /**
   * Get health history
   * @param {string} type - Database type
   * @param {number} limit - Number of records to return
   */
  getHealthHistory(type, limit = 10) {
    const history = this.healthHistory.get(type) || [];
    return history.slice(-limit);
  }

  /**
   * Get health metrics summary
   */
  getHealthMetrics() {
    const metrics = {
      uptime: {},
      averageResponseTime: {},
      failureRate: {},
      currentStatus: {}
    };

    this.healthChecks.forEach((health, type) => {
      const history = this.healthHistory.get(type) || [];

      // Calculate uptime
      const healthyChecks = history.filter(h => h.status === 'healthy').length;
      metrics.uptime[type] = history.length > 0 ? (healthyChecks / history.length) * 100 : 0;

      // Calculate average response time
      const responseTimes = history.map(h => h.responseTime);
      metrics.averageResponseTime[type] = responseTimes.length > 0 ?
        responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;

      // Calculate failure rate
      const failures = history.filter(h => h.status !== 'healthy').length;
      metrics.failureRate[type] = history.length > 0 ? (failures / history.length) * 100 : 0;

      // Current status
      metrics.currentStatus[type] = health.status;
    });

    return metrics;
  }

  /**
   * Set alert thresholds
   * @param {Object} thresholds - New alert thresholds
   */
  setAlertThresholds(thresholds) {
    this.alertThresholds = { ...this.alertThresholds, ...thresholds };
    logger.info('Alert thresholds updated:', this.alertThresholds);
    this.emit('thresholds_updated', this.alertThresholds);
  }

  /**
   * Clear health history
   * @param {string} type - Database type (optional)
   */
  clearHealthHistory(type = null) {
    if (type) {
      this.healthHistory.delete(type);
      logger.info(`Health history cleared for ${type}`);
    } else {
      this.healthHistory.clear();
      logger.info('All health history cleared');
    }
  }

  /**
   * Generate health report
   */
  generateHealthReport() {
    const report = {
      timestamp: new Date().toISOString(),
      monitoring: {
        active: this.isMonitoring,
        interval: this.checkInterval,
        alertThresholds: this.alertThresholds
      },
      summary: this.getHealthMetrics(),
      currentStatus: this.getHealthStatus(),
      alerts: this.getRecentAlerts()
    };

    return report;
  }

  /**
   * Get recent alerts (from event history if available)
   */
  getRecentAlerts() {
    // This would typically be implemented with a proper alert storage system
    // For now, return empty array as alerts are emitted as events
    return [];
  }

  /**
   * Destroy health monitor
   */
  destroy() {
    this.stopMonitoring();
    this.healthChecks.clear();
    this.healthHistory.clear();
    this.removeAllListeners();
    logger.info('Health monitor destroyed');
  }
}

module.exports = HealthMonitor;