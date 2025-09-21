/**
 * Connection Pool Manager
 * Advanced connection pooling and management for all database types
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
    new winston.transports.File({ filename: 'logs/connection-pool.log' })
  ]
});

class ConnectionPoolManager extends EventEmitter {
  constructor() {
    super();
    this.pools = new Map();
    this.poolConfigs = new Map();
    this.poolMetrics = new Map();
    this.isMonitoring = false;
    this.monitoringInterval = null;
  }

  /**
   * Register a database pool
   * @param {string} type - Database type
   * @param {IDatabaseManager} database - Database manager instance
   * @param {Object} config - Pool configuration
   */
  registerPool(type, database, config = {}) {
    const poolConfig = {
      ...this.getDefaultPoolConfig(type),
      ...config
    };

    this.pools.set(type, database);
    this.poolConfigs.set(type, poolConfig);
    this.initializePoolMetrics(type);

    logger.info(`Registered connection pool for ${type}`, poolConfig);
    this.emit('pool_registered', { type, config: poolConfig });
  }

  /**
   * Get default pool configuration for database type
   * @param {string} type - Database type
   */
  getDefaultPoolConfig(type) {
    const defaults = {
      postgresql: {
        maxConnections: 20,
        minConnections: 2,
        idleTimeoutMs: 30000,
        connectionTimeoutMs: 2000,
        acquireTimeoutMs: 60000,
        maxRetries: 3
      },
      clickhouse: {
        maxConnections: 10,
        minConnections: 1,
        idleTimeoutMs: 60000,
        connectionTimeoutMs: 5000,
        acquireTimeoutMs: 30000,
        maxRetries: 2
      },
      weaviate: {
        maxConnections: 5,
        minConnections: 1,
        idleTimeoutMs: 120000,
        connectionTimeoutMs: 10000,
        acquireTimeoutMs: 30000,
        maxRetries: 2
      },
      arangodb: {
        maxConnections: 15,
        minConnections: 2,
        idleTimeoutMs: 45000,
        connectionTimeoutMs: 3000,
        acquireTimeoutMs: 45000,
        maxRetries: 3
      },
      dragonflydb: {
        maxConnections: 50,
        minConnections: 5,
        idleTimeoutMs: 300000,
        connectionTimeoutMs: 1000,
        acquireTimeoutMs: 10000,
        maxRetries: 5
      }
    };

    return defaults[type] || defaults.postgresql;
  }

  /**
   * Initialize pool metrics
   * @param {string} type - Database type
   */
  initializePoolMetrics(type) {
    const metrics = {
      totalConnections: 0,
      activeConnections: 0,
      idleConnections: 0,
      waitingClients: 0,
      connectionsCreated: 0,
      connectionsDestroyed: 0,
      connectionErrors: 0,
      acquireCount: 0,
      acquireSuccessCount: 0,
      acquireFailureCount: 0,
      averageAcquireTime: 0,
      maxAcquireTime: 0,
      minAcquireTime: Infinity,
      lastAcquireTime: 0,
      poolUtilization: 0,
      errorRate: 0,
      throughput: 0,
      lastResetTime: Date.now()
    };

    this.poolMetrics.set(type, metrics);
  }

  /**
   * Update pool metrics
   * @param {string} type - Database type
   * @param {Object} statusUpdate - Status update data
   */
  updatePoolMetrics(type, statusUpdate) {
    const metrics = this.poolMetrics.get(type);
    if (!metrics) return;

    const database = this.pools.get(type);
    if (!database) return;

    try {
      const status = database.getStatus();

      // Update basic connection counts
      metrics.totalConnections = status.totalCount || 0;
      metrics.activeConnections = (status.totalCount || 0) - (status.idleCount || 0);
      metrics.idleConnections = status.idleCount || 0;
      metrics.waitingClients = status.waitingCount || 0;

      // Calculate pool utilization
      const config = this.poolConfigs.get(type);
      if (config && config.maxConnections > 0) {
        metrics.poolUtilization = (metrics.totalConnections / config.maxConnections) * 100;
      }

      // Update acquisition metrics if provided
      if (statusUpdate) {
        if (statusUpdate.acquireTime !== undefined) {
          metrics.acquireCount++;
          metrics.lastAcquireTime = statusUpdate.acquireTime;

          // Update min/max/average acquire times
          if (statusUpdate.acquireTime > metrics.maxAcquireTime) {
            metrics.maxAcquireTime = statusUpdate.acquireTime;
          }
          if (statusUpdate.acquireTime < metrics.minAcquireTime) {
            metrics.minAcquireTime = statusUpdate.acquireTime;
          }

          // Calculate running average
          if (metrics.acquireCount === 1) {
            metrics.averageAcquireTime = statusUpdate.acquireTime;
          } else {
            metrics.averageAcquireTime = (
              (metrics.averageAcquireTime * (metrics.acquireCount - 1)) + statusUpdate.acquireTime
            ) / metrics.acquireCount;
          }
        }

        if (statusUpdate.success !== undefined) {
          if (statusUpdate.success) {
            metrics.acquireSuccessCount++;
          } else {
            metrics.acquireFailureCount++;
            metrics.connectionErrors++;
          }
        }
      }

      // Calculate error rate
      if (metrics.acquireCount > 0) {
        metrics.errorRate = (metrics.acquireFailureCount / metrics.acquireCount) * 100;
      }

      // Calculate throughput (operations per second)
      const timeElapsed = (Date.now() - metrics.lastResetTime) / 1000;
      if (timeElapsed > 0) {
        metrics.throughput = metrics.acquireSuccessCount / timeElapsed;
      }

      this.emit('metrics_updated', { type, metrics });
    } catch (error) {
      logger.error(`Failed to update pool metrics for ${type}:`, error);
    }
  }

  /**
   * Get pool status
   * @param {string} type - Database type
   */
  getPoolStatus(type) {
    if (!this.pools.has(type)) {
      return null;
    }

    const database = this.pools.get(type);
    const config = this.poolConfigs.get(type);
    const metrics = this.poolMetrics.get(type);

    return {
      type,
      status: database.getStatus(),
      config,
      metrics,
      health: this.assessPoolHealth(type)
    };
  }

  /**
   * Get all pool statuses
   */
  getAllPoolStatuses() {
    const statuses = {};
    this.pools.forEach((database, type) => {
      statuses[type] = this.getPoolStatus(type);
    });
    return statuses;
  }

  /**
   * Assess pool health
   * @param {string} type - Database type
   */
  assessPoolHealth(type) {
    const metrics = this.poolMetrics.get(type);
    const config = this.poolConfigs.get(type);

    if (!metrics || !config) {
      return { status: 'unknown', issues: ['Missing metrics or configuration'] };
    }

    const issues = [];
    let status = 'healthy';

    // Check pool utilization
    if (metrics.poolUtilization > 90) {
      issues.push('High pool utilization (>90%)');
      status = 'warning';
    }

    // Check error rate
    if (metrics.errorRate > 5) {
      issues.push(`High error rate (${metrics.errorRate.toFixed(2)}%)`);
      status = status === 'healthy' ? 'warning' : 'critical';
    }

    // Check waiting clients
    if (metrics.waitingClients > 5) {
      issues.push(`High number of waiting clients (${metrics.waitingClients})`);
      status = status === 'healthy' ? 'warning' : status;
    }

    // Check average acquire time
    if (metrics.averageAcquireTime > config.acquireTimeoutMs * 0.5) {
      issues.push('High average connection acquire time');
      status = status === 'healthy' ? 'warning' : status;
    }

    // Check if pool is below minimum connections
    if (metrics.totalConnections < config.minConnections) {
      issues.push('Pool below minimum connection count');
      status = 'warning';
    }

    return { status, issues };
  }

  /**
   * Start pool monitoring
   * @param {number} intervalMs - Monitoring interval in milliseconds
   */
  startMonitoring(intervalMs = 30000) {
    if (this.isMonitoring) {
      logger.warn('Pool monitoring is already running');
      return;
    }

    this.isMonitoring = true;
    logger.info('Starting connection pool monitoring', { interval: intervalMs });

    this.monitoringInterval = setInterval(() => {
      this.updateAllPoolMetrics();
      this.checkPoolAlerts();
    }, intervalMs);

    this.emit('monitoring_started');
  }

  /**
   * Stop pool monitoring
   */
  stopMonitoring() {
    if (!this.isMonitoring) {
      return;
    }

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    this.isMonitoring = false;
    logger.info('Connection pool monitoring stopped');
    this.emit('monitoring_stopped');
  }

  /**
   * Update all pool metrics
   */
  updateAllPoolMetrics() {
    this.pools.forEach((database, type) => {
      this.updatePoolMetrics(type);
    });
  }

  /**
   * Check for pool alerts
   */
  checkPoolAlerts() {
    this.pools.forEach((database, type) => {
      const health = this.assessPoolHealth(type);
      const metrics = this.poolMetrics.get(type);

      if (health.status === 'warning' || health.status === 'critical') {
        const alert = {
          type: 'pool_health',
          database: type,
          severity: health.status,
          issues: health.issues,
          metrics: {
            utilization: metrics.poolUtilization,
            errorRate: metrics.errorRate,
            waitingClients: metrics.waitingClients,
            averageAcquireTime: metrics.averageAcquireTime
          },
          timestamp: new Date().toISOString()
        };

        logger.warn('Pool alert triggered:', alert);
        this.emit('pool_alert', alert);
      }
    });
  }

  /**
   * Optimize pool configuration based on metrics
   * @param {string} type - Database type
   */
  optimizePoolConfiguration(type) {
    const metrics = this.poolMetrics.get(type);
    const currentConfig = this.poolConfigs.get(type);

    if (!metrics || !currentConfig) {
      return null;
    }

    const recommendations = [];
    const newConfig = { ...currentConfig };

    // High utilization - increase max connections
    if (metrics.poolUtilization > 85 && metrics.errorRate < 1) {
      const newMax = Math.min(currentConfig.maxConnections * 1.2, 100);
      newConfig.maxConnections = Math.ceil(newMax);
      recommendations.push(`Increase max connections to ${newConfig.maxConnections}`);
    }

    // Low utilization - decrease max connections
    if (metrics.poolUtilization < 30 && currentConfig.maxConnections > 5) {
      const newMax = Math.max(currentConfig.maxConnections * 0.8, 5);
      newConfig.maxConnections = Math.ceil(newMax);
      recommendations.push(`Decrease max connections to ${newConfig.maxConnections}`);
    }

    // High wait times - adjust timeouts
    if (metrics.averageAcquireTime > currentConfig.acquireTimeoutMs * 0.7) {
      newConfig.acquireTimeoutMs = Math.min(currentConfig.acquireTimeoutMs * 1.5, 120000);
      recommendations.push(`Increase acquire timeout to ${newConfig.acquireTimeoutMs}ms`);
    }

    return {
      currentConfig,
      recommendedConfig: newConfig,
      recommendations,
      basedOnMetrics: {
        utilization: metrics.poolUtilization,
        errorRate: metrics.errorRate,
        averageAcquireTime: metrics.averageAcquireTime
      }
    };
  }

  /**
   * Apply optimized configuration
   * @param {string} type - Database type
   * @param {Object} newConfig - New configuration
   */
  applyConfiguration(type, newConfig) {
    this.poolConfigs.set(type, newConfig);
    logger.info(`Applied new pool configuration for ${type}:`, newConfig);
    this.emit('config_updated', { type, config: newConfig });
  }

  /**
   * Reset pool metrics
   * @param {string} type - Database type (optional)
   */
  resetMetrics(type = null) {
    if (type) {
      this.initializePoolMetrics(type);
      logger.info(`Pool metrics reset for ${type}`);
    } else {
      this.poolMetrics.forEach((metrics, dbType) => {
        this.initializePoolMetrics(dbType);
      });
      logger.info('All pool metrics reset');
    }
  }

  /**
   * Generate pool performance report
   */
  generatePerformanceReport() {
    const report = {
      timestamp: new Date().toISOString(),
      monitoring: this.isMonitoring,
      summary: {
        totalPools: this.pools.size,
        healthyPools: 0,
        warningPools: 0,
        criticalPools: 0
      },
      pools: {}
    };

    this.pools.forEach((database, type) => {
      const status = this.getPoolStatus(type);
      const health = this.assessPoolHealth(type);
      const optimization = this.optimizePoolConfiguration(type);

      report.pools[type] = {
        status,
        health,
        optimization
      };

      // Update summary
      switch (health.status) {
        case 'healthy':
          report.summary.healthyPools++;
          break;
        case 'warning':
          report.summary.warningPools++;
          break;
        case 'critical':
          report.summary.criticalPools++;
          break;
      }
    });

    return report;
  }

  /**
   * Destroy pool manager
   */
  destroy() {
    this.stopMonitoring();
    this.pools.clear();
    this.poolConfigs.clear();
    this.poolMetrics.clear();
    this.removeAllListeners();
    logger.info('Connection pool manager destroyed');
  }
}

module.exports = ConnectionPoolManager;