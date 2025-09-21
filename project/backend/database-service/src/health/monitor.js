const winston = require('winston');
const os = require('os');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class HealthMonitor {
  constructor(db) {
    this.db = db;
    this.startTime = Date.now();
    this.healthHistory = [];
    this.maxHistoryLength = 100;
  }

  async checkHealth() {
    const timestamp = new Date().toISOString();
    const health = {
      status: 'healthy',
      timestamp,
      service: 'database-service',
      version: '1.0.0',
      uptime: this.getUptime(),
      checks: {}
    };

    try {
      // Database connectivity check
      health.checks.database = await this.checkDatabase();

      // System resources check
      health.checks.system = await this.checkSystemResources();

      // Connection pool check
      health.checks.connectionPool = await this.checkConnectionPool();

      // Response time check
      health.checks.responseTime = await this.checkResponseTime();

      // Determine overall status
      const failedChecks = Object.values(health.checks).filter(check => check.status !== 'healthy');
      if (failedChecks.length > 0) {
        health.status = 'degraded';
        if (failedChecks.some(check => check.critical)) {
          health.status = 'unhealthy';
        }
      }

      // Store in history
      this.addToHistory(health);

      return health;
    } catch (error) {
      logger.error('Health check error:', error);
      health.status = 'unhealthy';
      health.error = error.message;
      return health;
    }
  }

  async checkDatabase() {
    const start = Date.now();
    try {
      const result = await this.db.query('SELECT NOW() as current_time, version() as version');
      const responseTime = Date.now() - start;

      return {
        status: 'healthy',
        responseTime: `${responseTime}ms`,
        details: {
          currentTime: result.rows[0].current_time,
          version: result.rows[0].version.split(' ')[0] // PostgreSQL version
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        critical: true,
        error: error.message,
        responseTime: `${Date.now() - start}ms`
      };
    }
  }

  async checkSystemResources() {
    try {
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const usedMemory = totalMemory - freeMemory;
      const memoryUsagePercent = Math.round((usedMemory / totalMemory) * 100);

      const loadAverage = os.loadavg();
      const cpuCount = os.cpus().length;

      const status = memoryUsagePercent > 90 ? 'unhealthy' :
                    memoryUsagePercent > 80 ? 'degraded' : 'healthy';

      return {
        status,
        critical: memoryUsagePercent > 95,
        details: {
          memory: {
            total: Math.round(totalMemory / 1024 / 1024 / 1024 * 100) / 100 + ' GB',
            used: Math.round(usedMemory / 1024 / 1024 / 1024 * 100) / 100 + ' GB',
            free: Math.round(freeMemory / 1024 / 1024 / 1024 * 100) / 100 + ' GB',
            usagePercent: memoryUsagePercent
          },
          cpu: {
            cores: cpuCount,
            loadAverage: {
              '1min': Math.round(loadAverage[0] * 100) / 100,
              '5min': Math.round(loadAverage[1] * 100) / 100,
              '15min': Math.round(loadAverage[2] * 100) / 100
            }
          },
          platform: os.platform(),
          uptime: Math.round(os.uptime())
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message
      };
    }
  }

  async checkConnectionPool() {
    try {
      const pool = this.db.getPool();
      const stats = {
        totalCount: pool.totalCount,
        idleCount: pool.idleCount,
        waitingCount: pool.waitingCount
      };

      const utilizationPercent = Math.round((stats.totalCount - stats.idleCount) / stats.totalCount * 100);

      const status = stats.waitingCount > 5 ? 'degraded' :
                    utilizationPercent > 90 ? 'degraded' : 'healthy';

      return {
        status,
        critical: stats.waitingCount > 20,
        details: {
          ...stats,
          utilizationPercent,
          maxConnections: process.env.DB_POOL_MAX || 20
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message
      };
    }
  }

  async checkResponseTime() {
    const start = Date.now();
    try {
      await this.db.query('SELECT 1');
      const responseTime = Date.now() - start;

      const status = responseTime > 1000 ? 'degraded' :
                    responseTime > 2000 ? 'unhealthy' : 'healthy';

      return {
        status,
        critical: responseTime > 5000,
        responseTime: `${responseTime}ms`,
        details: {
          threshold: {
            good: '< 1000ms',
            degraded: '1000-2000ms',
            unhealthy: '> 2000ms'
          }
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        critical: true,
        error: error.message,
        responseTime: `${Date.now() - start}ms`
      };
    }
  }

  getUptime() {
    const uptimeMs = Date.now() - this.startTime;
    const seconds = Math.floor(uptimeMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}d ${hours % 24}h ${minutes % 60}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  addToHistory(health) {
    this.healthHistory.push({
      timestamp: health.timestamp,
      status: health.status,
      responseTime: health.checks.responseTime?.responseTime,
      memoryUsage: health.checks.system?.details?.memory?.usagePercent
    });

    // Keep only recent history
    if (this.healthHistory.length > this.maxHistoryLength) {
      this.healthHistory = this.healthHistory.slice(-this.maxHistoryLength);
    }
  }

  getHealthHistory() {
    return this.healthHistory;
  }

  getHealthSummary() {
    if (this.healthHistory.length === 0) {
      return { status: 'no_data' };
    }

    const recent = this.healthHistory.slice(-10);
    const healthyCount = recent.filter(h => h.status === 'healthy').length;
    const degradedCount = recent.filter(h => h.status === 'degraded').length;
    const unhealthyCount = recent.filter(h => h.status === 'unhealthy').length;

    return {
      recentChecks: recent.length,
      healthy: healthyCount,
      degraded: degradedCount,
      unhealthy: unhealthyCount,
      healthPercentage: Math.round((healthyCount / recent.length) * 100)
    };
  }
}

module.exports = HealthMonitor;