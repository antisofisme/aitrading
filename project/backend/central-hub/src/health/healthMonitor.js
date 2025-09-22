/**
 * Health Monitor - System-wide health monitoring and alerting
 */

const EventEmitter = require('events');

class HealthMonitor extends EventEmitter {
  constructor() {
    super();
    this.healthChecks = new Map();
    this.thresholds = {
      responseTime: 5000, // 5 seconds
      errorRate: 0.05, // 5%
      cpuUsage: 0.8, // 80%
      memoryUsage: 0.85 // 85%
    };
    this.isRunning = false;
  }

  async start() {
    if (this.isRunning) {
      return;
    }

    console.log('Starting Health Monitor...');
    this.isRunning = true;

    // Start periodic health monitoring
    this.monitoringInterval = setInterval(() => {
      this.performSystemHealthCheck();
    }, 30000); // Every 30 seconds

    console.log('Health Monitor started successfully');
  }

  async stop() {
    if (!this.isRunning) {
      return;
    }

    console.log('Stopping Health Monitor...');
    this.isRunning = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    console.log('Health Monitor stopped');
  }

  async checkService(serviceName) {
    try {
      // In a real implementation, this would make actual HTTP requests
      // For now, we'll simulate health checks
      const startTime = Date.now();

      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, Math.random() * 100));

      const responseTime = Date.now() - startTime;
      const isHealthy = Math.random() > 0.1; // 90% success rate simulation

      const healthCheck = {
        service: serviceName,
        status: isHealthy ? 'healthy' : 'unhealthy',
        responseTime,
        timestamp: new Date().toISOString(),
        checks: {
          connectivity: isHealthy,
          responseTime: responseTime < this.thresholds.responseTime,
          database: Math.random() > 0.05, // 95% database connectivity
          dependencies: Math.random() > 0.08 // 92% dependency availability
        }
      };

      this.healthChecks.set(serviceName, healthCheck);

      if (!isHealthy) {
        this.emit('serviceUnhealthy', healthCheck);
      }

      return healthCheck;
    } catch (error) {
      const healthCheck = {
        service: serviceName,
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };

      this.healthChecks.set(serviceName, healthCheck);
      this.emit('serviceError', healthCheck);

      return healthCheck;
    }
  }

  async performSystemHealthCheck() {
    try {
      const systemHealth = {
        timestamp: new Date().toISOString(),
        system: await this.getSystemMetrics(),
        services: {},
        alerts: []
      };

      // Mock service health checks
      const services = ['api-gateway', 'database-service', 'data-bridge', 'central-hub'];

      for (const service of services) {
        const health = await this.checkService(service);
        systemHealth.services[service] = health;

        // Check for alerts
        if (health.status !== 'healthy') {
          systemHealth.alerts.push({
            type: 'service_unhealthy',
            service,
            message: `Service ${service} is ${health.status}`,
            severity: 'high',
            timestamp: health.timestamp
          });
        }

        if (health.responseTime > this.thresholds.responseTime) {
          systemHealth.alerts.push({
            type: 'slow_response',
            service,
            message: `Service ${service} response time ${health.responseTime}ms exceeds threshold`,
            severity: 'medium',
            timestamp: health.timestamp
          });
        }
      }

      // System-level alerts
      if (systemHealth.system.cpu.usage > this.thresholds.cpuUsage) {
        systemHealth.alerts.push({
          type: 'high_cpu',
          message: `CPU usage ${(systemHealth.system.cpu.usage * 100).toFixed(2)}% exceeds threshold`,
          severity: 'high',
          timestamp: systemHealth.timestamp
        });
      }

      if (systemHealth.system.memory.usage > this.thresholds.memoryUsage) {
        systemHealth.alerts.push({
          type: 'high_memory',
          message: `Memory usage ${(systemHealth.system.memory.usage * 100).toFixed(2)}% exceeds threshold`,
          severity: 'high',
          timestamp: systemHealth.timestamp
        });
      }

      // Emit alerts
      systemHealth.alerts.forEach(alert => {
        this.emit('alert', alert);
      });

      return systemHealth;
    } catch (error) {
      console.error('System health check failed:', error);
      throw error;
    }
  }

  async getSystemMetrics() {
    const memUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();

    return {
      uptime: process.uptime(),
      cpu: {
        user: cpuUsage.user,
        system: cpuUsage.system,
        usage: Math.random() * 0.6 + 0.1 // Mock CPU usage between 10-70%
      },
      memory: {
        total: memUsage.heapTotal,
        used: memUsage.heapUsed,
        free: memUsage.heapTotal - memUsage.heapUsed,
        usage: memUsage.heapUsed / memUsage.heapTotal,
        external: memUsage.external,
        rss: memUsage.rss
      },
      load: {
        average1: Math.random() * 2, // Mock load averages
        average5: Math.random() * 2,
        average15: Math.random() * 2
      },
      disk: {
        usage: Math.random() * 0.5 + 0.2 // Mock disk usage 20-70%
      }
    };
  }

  async getHealthSummary() {
    const services = Array.from(this.healthChecks.values());
    const healthyServices = services.filter(s => s.status === 'healthy').length;
    const totalServices = services.length;
    const systemMetrics = await this.getSystemMetrics();

    return {
      overall: healthyServices === totalServices ? 'healthy' : 'degraded',
      services: {
        total: totalServices,
        healthy: healthyServices,
        unhealthy: totalServices - healthyServices
      },
      system: {
        cpu: systemMetrics.cpu.usage,
        memory: systemMetrics.memory.usage,
        uptime: systemMetrics.uptime
      },
      lastCheck: new Date().toISOString()
    };
  }

  setThreshold(metric, value) {
    if (this.thresholds.hasOwnProperty(metric)) {
      this.thresholds[metric] = value;
      console.log(`Threshold updated: ${metric} = ${value}`);
    } else {
      throw new Error(`Unknown threshold metric: ${metric}`);
    }
  }

  getThresholds() {
    return { ...this.thresholds };
  }

  // Event handlers
  onServiceUnhealthy(callback) {
    this.on('serviceUnhealthy', callback);
  }

  onServiceError(callback) {
    this.on('serviceError', callback);
  }

  onAlert(callback) {
    this.on('alert', callback);
  }
}

module.exports = HealthMonitor;