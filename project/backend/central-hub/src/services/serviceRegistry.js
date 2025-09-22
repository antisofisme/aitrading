/**
 * Service Registry - Central coordination for microservices
 * Manages service discovery, health monitoring, and coordination
 */

const EventEmitter = require('events');

class ServiceRegistry extends EventEmitter {
  constructor() {
    super();
    this.services = new Map();
    this.serviceHealthCache = new Map();
    this.coordinationRules = new Map();
    this.isInitialized = false;
  }

  async initialize() {
    try {
      console.log('Initializing Service Registry...');

      // Setup coordination rules
      this.setupCoordinationRules();

      // Start periodic health checks
      this.startHealthMonitoring();

      this.isInitialized = true;
      console.log('Service Registry initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Service Registry:', error);
      throw error;
    }
  }

  setupCoordinationRules() {
    // Define service coordination rules
    this.coordinationRules.set('api-gateway', {
      dependencies: ['database-service', 'central-hub'],
      healthCheckInterval: 30000,
      maxRetries: 3
    });

    this.coordinationRules.set('database-service', {
      dependencies: [],
      healthCheckInterval: 30000,
      maxRetries: 5
    });

    this.coordinationRules.set('data-bridge', {
      dependencies: ['database-service'],
      healthCheckInterval: 15000,
      maxRetries: 3
    });

    this.coordinationRules.set('central-hub', {
      dependencies: ['database-service'],
      healthCheckInterval: 30000,
      maxRetries: 3
    });
  }

  async registerService(serviceConfig) {
    const {
      name,
      host = 'localhost',
      port,
      health,
      endpoints = [],
      metadata = {}
    } = serviceConfig;

    if (!name || !port) {
      throw new Error('Service name and port are required');
    }

    const service = {
      name,
      host,
      port,
      health: health || `http://${host}:${port}/health`,
      endpoints,
      metadata,
      registeredAt: new Date().toISOString(),
      lastHealthCheck: null,
      status: 'registered',
      retryCount: 0
    };

    this.services.set(name, service);

    // Emit service registered event
    this.emit('serviceRegistered', service);

    console.log(`Service registered: ${name} at ${host}:${port}`);

    // Perform initial health check
    await this.checkServiceHealth(name);

    return service;
  }

  async deregisterService(serviceName) {
    if (!this.services.has(serviceName)) {
      throw new Error(`Service not found: ${serviceName}`);
    }

    const service = this.services.get(serviceName);
    this.services.delete(serviceName);
    this.serviceHealthCache.delete(serviceName);

    // Emit service deregistered event
    this.emit('serviceDeregistered', service);

    console.log(`Service deregistered: ${serviceName}`);

    return service;
  }

  async getServices() {
    return Array.from(this.services.values());
  }

  async getService(serviceName) {
    return this.services.get(serviceName) || null;
  }

  async getHealthyServices() {
    const services = await this.getServices();
    return services.filter(service => service.status === 'healthy');
  }

  async checkServiceHealth(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      throw new Error(`Service not found: ${serviceName}`);
    }

    try {
      // Simple HTTP health check (in real implementation, use axios or fetch)
      const healthCheck = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        responseTime: Math.floor(Math.random() * 100) + 10 // Mock response time
      };

      service.lastHealthCheck = healthCheck.timestamp;
      service.status = 'healthy';
      service.retryCount = 0;

      this.serviceHealthCache.set(serviceName, healthCheck);

      // Emit health check success
      this.emit('healthCheckSuccess', { service: serviceName, health: healthCheck });

      return healthCheck;
    } catch (error) {
      service.status = 'unhealthy';
      service.retryCount = (service.retryCount || 0) + 1;

      const healthCheck = {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error.message,
        retryCount: service.retryCount
      };

      this.serviceHealthCache.set(serviceName, healthCheck);

      // Emit health check failure
      this.emit('healthCheckFailure', { service: serviceName, health: healthCheck });

      return healthCheck;
    }
  }

  startHealthMonitoring() {
    // Check all services health periodically
    setInterval(async () => {
      const services = await this.getServices();

      for (const service of services) {
        const rules = this.coordinationRules.get(service.name);
        const interval = rules?.healthCheckInterval || 30000;
        const maxRetries = rules?.maxRetries || 3;

        // Check if it's time for health check
        const lastCheck = new Date(service.lastHealthCheck || 0);
        const now = new Date();

        if (now - lastCheck >= interval) {
          try {
            await this.checkServiceHealth(service.name);
          } catch (error) {
            console.error(`Health check failed for ${service.name}:`, error);

            // Handle service failure based on retry count
            if (service.retryCount >= maxRetries) {
              this.emit('serviceFailure', { service: service.name, retries: service.retryCount });
            }
          }
        }
      }
    }, 10000); // Check every 10 seconds
  }

  async restartService(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      throw new Error(`Service not found: ${serviceName}`);
    }

    console.log(`Initiating restart for service: ${serviceName}`);

    // In a real implementation, this would trigger actual service restart
    // For now, we'll simulate a restart process
    service.status = 'restarting';
    service.retryCount = 0;

    // Emit restart event
    this.emit('serviceRestart', { service: serviceName });

    // Simulate restart delay
    setTimeout(async () => {
      await this.checkServiceHealth(serviceName);
    }, 5000);

    return {
      service: serviceName,
      action: 'restart_initiated',
      timestamp: new Date().toISOString()
    };
  }

  async getServiceDependencies(serviceName) {
    const rules = this.coordinationRules.get(serviceName);
    return rules?.dependencies || [];
  }

  async validateDependencies(serviceName) {
    const dependencies = await this.getServiceDependencies(serviceName);
    const results = [];

    for (const dependency of dependencies) {
      const service = this.services.get(dependency);
      if (!service) {
        results.push({
          service: dependency,
          status: 'missing',
          available: false
        });
      } else {
        const health = this.serviceHealthCache.get(dependency);
        results.push({
          service: dependency,
          status: health?.status || 'unknown',
          available: health?.status === 'healthy'
        });
      }
    }

    return {
      service: serviceName,
      dependencies: results,
      allAvailable: results.every(r => r.available)
    };
  }

  async getServiceMetrics() {
    const services = await this.getServices();
    const healthyCount = services.filter(s => s.status === 'healthy').length;
    const unhealthyCount = services.filter(s => s.status === 'unhealthy').length;

    return {
      total: services.length,
      healthy: healthyCount,
      unhealthy: unhealthyCount,
      registryUptime: process.uptime(),
      services: services.map(s => ({
        name: s.name,
        status: s.status,
        lastHealthCheck: s.lastHealthCheck,
        retryCount: s.retryCount
      }))
    };
  }

  // Event handlers for service coordination
  onServiceRegistered(callback) {
    this.on('serviceRegistered', callback);
  }

  onServiceDeregistered(callback) {
    this.on('serviceDeregistered', callback);
  }

  onHealthCheckSuccess(callback) {
    this.on('healthCheckSuccess', callback);
  }

  onHealthCheckFailure(callback) {
    this.on('healthCheckFailure', callback);
  }

  onServiceFailure(callback) {
    this.on('serviceFailure', callback);
  }

  onServiceRestart(callback) {
    this.on('serviceRestart', callback);
  }
}

module.exports = ServiceRegistry;