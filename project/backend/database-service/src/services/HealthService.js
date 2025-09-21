const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

class HealthService {
  constructor(db) {
    this.db = db;
    this.startTime = Date.now();
    this.lastHealthCheck = null;
    this.healthMetrics = {
      totalQueries: 0,
      errorCount: 0,
      averageResponseTime: 0,
      connectionPoolStats: {}
    };
  }

  async checkDatabaseHealth() {
    try {
      const start = Date.now();

      // Test basic connection
      await this.db.query('SELECT 1 as health_check');

      // Test users table
      await this.db.query('SELECT COUNT(*) FROM users');

      const responseTime = Date.now() - start;

      this.lastHealthCheck = {
        timestamp: new Date(),
        status: 'healthy',
        responseTime,
        poolStats: this.db.getStatus()
      };

      return this.lastHealthCheck;

    } catch (error) {
      logger.error('Database health check failed:', error);

      this.lastHealthCheck = {
        timestamp: new Date(),
        status: 'unhealthy',
        error: error.message,
        poolStats: this.db.getStatus()
      };

      return this.lastHealthCheck;
    }
  }

  async getDetailedHealth() {
    const dbHealth = await this.checkDatabaseHealth();
    const uptime = Date.now() - this.startTime;

    return {
      service: 'database-service',
      status: dbHealth.status,
      uptime: {
        seconds: Math.floor(uptime / 1000),
        human: this.formatUptime(uptime)
      },
      database: dbHealth,
      metrics: this.healthMetrics,
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0'
    };
  }

  formatUptime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  }

  recordQuery(responseTime, success = true) {
    this.healthMetrics.totalQueries++;

    if (!success) {
      this.healthMetrics.errorCount++;
    }

    // Calculate rolling average response time
    const alpha = 0.1; // Smoothing factor
    this.healthMetrics.averageResponseTime =
      this.healthMetrics.averageResponseTime * (1 - alpha) +
      responseTime * alpha;
  }

  async checkExternalServices() {
    const services = [];

    // Check Central Hub connection
    try {
      const axios = require('axios');
      const hubUrl = process.env.CENTRAL_HUB_URL || 'http://localhost:8000';

      const start = Date.now();
      await axios.get(`${hubUrl}/health`, { timeout: 5000 });
      const responseTime = Date.now() - start;

      services.push({
        name: 'central-hub',
        status: 'healthy',
        responseTime,
        url: hubUrl
      });

    } catch (error) {
      services.push({
        name: 'central-hub',
        status: 'unhealthy',
        error: error.message,
        url: process.env.CENTRAL_HUB_URL || 'http://localhost:8000'
      });
    }

    return services;
  }

  async getFullHealthReport() {
    const [basicHealth, externalServices] = await Promise.all([
      this.getDetailedHealth(),
      this.checkExternalServices()
    ]);

    return {
      ...basicHealth,
      externalServices,
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        memory: process.memoryUsage(),
        pid: process.pid
      }
    };
  }

  isHealthy() {
    return this.lastHealthCheck && this.lastHealthCheck.status === 'healthy';
  }

  getErrorRate() {
    if (this.healthMetrics.totalQueries === 0) return 0;
    return (this.healthMetrics.errorCount / this.healthMetrics.totalQueries) * 100;
  }
}

module.exports = HealthService;