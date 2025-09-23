/**
 * Service Coordinator - Manages communication between AI services
 * Handles health checks, service discovery, and inter-service communication
 */

const axios = require('axios');
const EventEmitter = require('events');

class ServiceCoordinator extends EventEmitter {
  constructor(logger) {
    super();
    this.logger = logger;
    this.services = new Map();
    this.healthCheckInterval = null;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // Register known services
      await this.registerKnownServices();
      
      // Start health monitoring
      this.startHealthMonitoring();
      
      this.isInitialized = true;
      this.logger.info('Service Coordinator initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Service Coordinator', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  async registerKnownServices() {
    const knownServices = [
      { name: 'configuration-service', port: 8012, critical: true },
      { name: 'database-service', port: 8008, critical: true },
      { name: 'feature-engineering', port: 8011, critical: false },
      { name: 'ml-automl', port: 8013, critical: false },
      { name: 'pattern-validator', port: 8015, critical: false },
      { name: 'telegram-service', port: 8016, critical: false },
      { name: 'realtime-inference-engine', port: 8017, critical: false },
      { name: 'ml-ensemble', port: 8021, critical: false },
      { name: 'backtesting-engine', port: 8024, critical: false },
      { name: 'performance-analytics', port: 8002, critical: false },
      { name: 'revenue-analytics', port: 8026, critical: false },
      { name: 'usage-monitoring', port: 8027, critical: false },
      { name: 'compliance-monitor', port: 8040, critical: false }
    ];

    for (const service of knownServices) {
      this.services.set(service.name, {
        ...service,
        status: 'unknown',
        lastHealthCheck: null,
        consecutiveFailures: 0,
        isAvailable: false
      });
    }

    this.logger.info('Registered known services', {
      serviceCount: this.services.size,
      services: Array.from(this.services.keys())
    });
  }

  startHealthMonitoring() {
    // Check health every 30 seconds
    this.healthCheckInterval = setInterval(async () => {
      await this.performHealthChecks();
    }, 30000);

    this.logger.info('Health monitoring started');
  }

  async performHealthChecks() {
    const healthPromises = Array.from(this.services.entries()).map(async ([serviceName, serviceInfo]) => {
      try {
        const health = await this.checkServiceHealth(serviceName, serviceInfo.port);
        
        this.services.set(serviceName, {
          ...serviceInfo,
          status: health.status,
          lastHealthCheck: Date.now(),
          consecutiveFailures: health.status === 'healthy' ? 0 : serviceInfo.consecutiveFailures + 1,
          isAvailable: health.status === 'healthy',
          health: health.health
        });

      } catch (error) {
        this.services.set(serviceName, {
          ...serviceInfo,
          status: 'unhealthy',
          lastHealthCheck: Date.now(),
          consecutiveFailures: serviceInfo.consecutiveFailures + 1,
          isAvailable: false,
          error: error.message
        });
      }
    });

    await Promise.allSettled(healthPromises);
  }

  async checkServiceHealth(serviceName, port) {
    try {
      const url = `http://localhost:${port}/health`;
      const response = await axios.get(url, { 
        timeout: 5000,
        headers: {
          'X-Health-Check': 'ai-orchestrator'
        }
      });

      if (response.status === 200) {
        return {
          status: 'healthy',
          health: response.data,
          responseTime: response.headers['x-response-time'] || 'unknown'
        };
      } else {
        return {
          status: 'unhealthy',
          health: null,
          error: `HTTP ${response.status}`
        };
      }
    } catch (error) {
      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        return {
          status: 'unavailable',
          health: null,
          error: 'Service not running'
        };
      }
      
      return {
        status: 'unhealthy',
        health: null,
        error: error.message
      };
    }
  }

  async getDetailedHealth(serviceName, port) {
    try {
      const basicHealth = await this.checkServiceHealth(serviceName, port);
      
      if (basicHealth.status === 'healthy') {
        // Try to get more detailed health info
        try {
          const detailedUrl = `http://localhost:${port}/api/status`;
          const detailedResponse = await axios.get(detailedUrl, { timeout: 3000 });
          
          return {
            ...basicHealth,
            detailedHealth: detailedResponse.data,
            capabilities: detailedResponse.data.capabilities || [],
            performance: detailedResponse.data.performance || {}
          };
        } catch (detailedError) {
          // If detailed endpoint is not available, return basic health
          return basicHealth;
        }
      }
      
      return basicHealth;
      
    } catch (error) {
      return {
        status: 'error',
        error: error.message,
        lastCheck: new Date().toISOString()
      };
    }
  }

  async coordinateServiceCall(serviceName, endpoint, payload, options = {}) {
    const service = this.services.get(serviceName);
    
    if (!service) {
      throw new Error(`Service ${serviceName} not registered`);
    }

    if (!service.isAvailable && options.requireAvailable !== false) {
      throw new Error(`Service ${serviceName} is not available`);
    }

    try {
      const url = `http://localhost:${service.port}${endpoint}`;
      const response = await axios.post(url, payload, {
        timeout: options.timeout || 30000,
        headers: {
          'Content-Type': 'application/json',
          'X-Orchestrator': 'ai-orchestrator',
          'X-Correlation-Id': options.correlationId || this.generateCorrelationId(),
          ...options.headers
        }
      });

      // Update service health based on successful call
      this.services.set(serviceName, {
        ...service,
        consecutiveFailures: 0,
        lastSuccessfulCall: Date.now()
      });

      return response.data;

    } catch (error) {
      // Update service health based on failed call
      this.services.set(serviceName, {
        ...service,
        consecutiveFailures: service.consecutiveFailures + 1,
        lastFailedCall: Date.now()
      });

      this.logger.error('Service call failed', {
        serviceName,
        endpoint,
        error: error.message,
        consecutiveFailures: service.consecutiveFailures + 1
      });

      throw error;
    }
  }

  async broadcastToServices(services, endpoint, payload, options = {}) {
    const results = new Map();
    const errors = new Map();

    const broadcastPromises = services.map(async (serviceName) => {
      try {
        const result = await this.coordinateServiceCall(serviceName, endpoint, payload, {
          ...options,
          requireAvailable: false // Allow calls to unavailable services for broadcasting
        });
        results.set(serviceName, result);
      } catch (error) {
        errors.set(serviceName, error.message);
      }
    });

    await Promise.allSettled(broadcastPromises);

    return {
      successful: Object.fromEntries(results),
      failed: Object.fromEntries(errors),
      successCount: results.size,
      failureCount: errors.size
    };
  }

  getServiceStatus(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      return { status: 'not-registered' };
    }

    return {
      status: service.status,
      isAvailable: service.isAvailable,
      lastHealthCheck: service.lastHealthCheck,
      consecutiveFailures: service.consecutiveFailures,
      port: service.port,
      critical: service.critical
    };
  }

  getAllServicesStatus() {
    const status = {};
    
    this.services.forEach((service, name) => {
      status[name] = {
        status: service.status,
        isAvailable: service.isAvailable,
        lastHealthCheck: service.lastHealthCheck,
        consecutiveFailures: service.consecutiveFailures,
        port: service.port,
        critical: service.critical
      };
    });

    return status;
  }

  getCriticalServicesHealth() {
    const criticalServices = Array.from(this.services.entries())
      .filter(([, service]) => service.critical);
    
    const unhealthyCritical = criticalServices
      .filter(([, service]) => !service.isAvailable)
      .map(([name]) => name);

    return {
      totalCritical: criticalServices.length,
      healthyCritical: criticalServices.length - unhealthyCritical.length,
      unhealthyCritical,
      overallHealth: unhealthyCritical.length === 0 ? 'healthy' : 'critical'
    };
  }

  generateCorrelationId() {
    return `orchestrator_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  isHealthy() {
    const criticalHealth = this.getCriticalServicesHealth();
    return this.isInitialized && criticalHealth.overallHealth !== 'critical';
  }

  getMetrics() {
    const allStatus = this.getAllServicesStatus();
    const totalServices = Object.keys(allStatus).length;
    const availableServices = Object.values(allStatus).filter(s => s.isAvailable).length;
    const criticalHealth = this.getCriticalServicesHealth();

    return {
      totalServices,
      availableServices,
      unavailableServices: totalServices - availableServices,
      criticalServicesHealth: criticalHealth,
      healthCheckInterval: 30000,
      lastFullHealthCheck: Math.max(...Object.values(allStatus).map(s => s.lastHealthCheck || 0))
    };
  }

  async shutdown() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    
    this.logger.info('Service Coordinator shut down');
  }
}

module.exports = ServiceCoordinator;