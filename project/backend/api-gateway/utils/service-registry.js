const Redis = require('redis');
const axios = require('axios');
const logger = require('./logger');
const config = require('../config/gateway.config');

class ServiceRegistry {
  constructor() {
    this.redis = null;
    this.services = new Map();
    this.healthCheckInterval = null;
    this.initialized = false;
  }

  async initialize() {
    try {
      // Initialize Redis connection
      this.redis = Redis.createClient({
        host: config.redis.host,
        port: config.redis.port,
        password: config.redis.password,
        db: config.redis.db
      });

      await this.redis.connect();
      logger.info('Connected to Redis for service registry');

      // Load existing services from Redis
      await this.loadServicesFromRedis();

      // Start health check monitoring
      this.startHealthChecking();

      this.initialized = true;
      logger.info('Service registry initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize service registry:', error);
      // Continue without Redis (in-memory mode)
      this.initializeDefaultServices();
      this.initialized = true;
    }
  }

  async loadServicesFromRedis() {
    try {
      if (!this.redis) return;

      const serviceKeys = await this.redis.keys('service:*');
      for (const key of serviceKeys) {
        const serviceData = await this.redis.get(key);
        if (serviceData) {
          const service = JSON.parse(serviceData);
          this.services.set(service.name, service);
        }
      }

      logger.info(`Loaded ${this.services.size} services from Redis`);
    } catch (error) {
      logger.error('Failed to load services from Redis:', error);
    }
  }

  initializeDefaultServices() {
    // Initialize with configured services
    Object.entries(config.services).forEach(([name, serviceConfig]) => {
      this.services.set(name, {
        name,
        url: serviceConfig.url,
        health: `${serviceConfig.url}/health`,
        timeout: serviceConfig.timeout,
        version: '1.0.0',
        status: 'unknown',
        lastCheck: null,
        metadata: {
          type: 'microservice',
          environment: process.env.NODE_ENV || 'development'
        },
        registeredAt: new Date().toISOString()
      });
    });

    logger.info(`Initialized ${this.services.size} default services`);
  }

  async register(serviceInfo) {
    try {
      const service = {
        name: serviceInfo.name,
        url: serviceInfo.url,
        health: serviceInfo.health || `${serviceInfo.url}/health`,
        version: serviceInfo.version || '1.0.0',
        timeout: serviceInfo.timeout || 30000,
        status: 'unknown',
        lastCheck: null,
        metadata: serviceInfo.metadata || {},
        registeredAt: new Date().toISOString(),
        registeredBy: serviceInfo.registeredBy || 'system'
      };

      // Store in memory
      this.services.set(service.name, service);

      // Store in Redis
      if (this.redis) {
        await this.redis.set(
          `service:${service.name}`,
          JSON.stringify(service),
          'EX',
          86400 // 24 hours TTL
        );
      }

      // Perform initial health check
      await this.checkHealth(service.name);

      logger.info(`Service registered: ${service.name} at ${service.url}`);
      return service;
    } catch (error) {
      logger.error('Failed to register service:', error);
      throw error;
    }
  }

  async unregister(serviceName) {
    try {
      // Remove from memory
      const deleted = this.services.delete(serviceName);

      // Remove from Redis
      if (this.redis) {
        await this.redis.del(`service:${serviceName}`);
      }

      if (deleted) {
        logger.info(`Service unregistered: ${serviceName}`);
      }

      return deleted;
    } catch (error) {
      logger.error('Failed to unregister service:', error);
      throw error;
    }
  }

  async update(serviceName, updates) {
    try {
      const service = this.services.get(serviceName);
      if (!service) {
        return null;
      }

      const updatedService = {
        ...service,
        ...updates,
        updatedAt: new Date().toISOString()
      };

      // Update in memory
      this.services.set(serviceName, updatedService);

      // Update in Redis
      if (this.redis) {
        await this.redis.set(
          `service:${serviceName}`,
          JSON.stringify(updatedService),
          'EX',
          86400
        );
      }

      logger.info(`Service updated: ${serviceName}`);
      return updatedService;
    } catch (error) {
      logger.error('Failed to update service:', error);
      throw error;
    }
  }

  async checkHealth(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      return null;
    }

    const startTime = Date.now();
    let healthStatus = {
      service: serviceName,
      status: 'unhealthy',
      responseTime: null,
      lastCheck: new Date().toISOString(),
      error: null
    };

    try {
      const response = await axios.get(service.health, {
        timeout: service.timeout || 30000,
        validateStatus: () => true // Don't throw on non-2xx status
      });

      const responseTime = Date.now() - startTime;

      healthStatus = {
        service: serviceName,
        status: response.status === 200 ? 'healthy' : 'unhealthy',
        statusCode: response.status,
        responseTime: `${responseTime}ms`,
        lastCheck: new Date().toISOString(),
        data: response.data,
        error: response.status !== 200 ? `HTTP ${response.status}` : null
      };

      // Update service status
      service.status = healthStatus.status;
      service.lastCheck = healthStatus.lastCheck;
      service.responseTime = responseTime;

    } catch (error) {
      const responseTime = Date.now() - startTime;

      healthStatus = {
        service: serviceName,
        status: 'unhealthy',
        responseTime: `${responseTime}ms`,
        lastCheck: new Date().toISOString(),
        error: error.code || error.message
      };

      // Update service status
      service.status = 'unhealthy';
      service.lastCheck = healthStatus.lastCheck;
      service.error = error.message;

      logger.warn(`Health check failed for ${serviceName}:`, error.message);
    }

    // Update in Redis
    if (this.redis) {
      try {
        await this.redis.set(
          `service:${serviceName}`,
          JSON.stringify(service),
          'EX',
          86400
        );

        await this.redis.set(
          `health:${serviceName}`,
          JSON.stringify(healthStatus),
          'EX',
          300 // 5 minutes
        );
      } catch (redisError) {
        logger.error('Failed to update service health in Redis:', redisError);
      }
    }

    return healthStatus;
  }

  async forceHealthCheck(serviceName) {
    return await this.checkHealth(serviceName);
  }

  async getAllServices() {
    const servicesObject = {};

    for (const [name, service] of this.services) {
      servicesObject[name] = {
        ...service,
        uptime: service.lastCheck ?
          Date.now() - new Date(service.registeredAt).getTime() : 0
      };
    }

    return servicesObject;
  }

  async getService(serviceName) {
    return this.services.get(serviceName) || null;
  }

  async getHealthyServices() {
    const healthyServices = {};

    for (const [name, service] of this.services) {
      if (service.status === 'healthy') {
        healthyServices[name] = service;
      }
    }

    return healthyServices;
  }

  async getServiceByType(type) {
    const matchingServices = {};

    for (const [name, service] of this.services) {
      if (service.metadata?.type === type) {
        matchingServices[name] = service;
      }
    }

    return matchingServices;
  }

  startHealthChecking() {
    const interval = config.monitoring?.healthCheckInterval || 30000;

    this.healthCheckInterval = setInterval(async () => {
      logger.debug('Running periodic health checks...');

      const checks = Array.from(this.services.keys()).map(serviceName =>
        this.checkHealth(serviceName).catch(error => {
          logger.error(`Health check error for ${serviceName}:`, error);
        })
      );

      await Promise.all(checks);
      logger.debug('Periodic health checks completed');
    }, interval);

    logger.info(`Started health checking with ${interval}ms interval`);
  }

  stopHealthChecking() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
      logger.info('Stopped health checking');
    }
  }

  async cleanup() {
    try {
      this.stopHealthChecking();

      if (this.redis) {
        await this.redis.disconnect();
        logger.info('Disconnected from Redis');
      }

      this.services.clear();
      logger.info('Service registry cleanup completed');
    } catch (error) {
      logger.error('Service registry cleanup error:', error);
    }
  }

  // Circuit breaker functionality
  async isServiceHealthy(serviceName, threshold = 3) {
    const service = this.services.get(serviceName);
    if (!service) return false;

    // Check if service has been failing consistently
    try {
      if (this.redis) {
        const failureCount = await this.redis.get(`failures:${serviceName}`) || 0;
        return parseInt(failureCount) < threshold;
      }
    } catch (error) {
      logger.error('Failed to check service failure count:', error);
    }

    return service.status === 'healthy';
  }

  async recordFailure(serviceName) {
    try {
      if (this.redis) {
        await this.redis.incr(`failures:${serviceName}`);
        await this.redis.expire(`failures:${serviceName}`, 300); // 5 minutes
      }
    } catch (error) {
      logger.error('Failed to record service failure:', error);
    }
  }

  async clearFailures(serviceName) {
    try {
      if (this.redis) {
        await this.redis.del(`failures:${serviceName}`);
      }
    } catch (error) {
      logger.error('Failed to clear service failures:', error);
    }
  }
}

module.exports = ServiceRegistry;