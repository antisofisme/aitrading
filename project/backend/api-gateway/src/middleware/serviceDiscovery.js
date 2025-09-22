const axios = require('axios');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'api-gateway-service-discovery' }
});

// Service health cache
const serviceHealthCache = new Map();
const HEALTH_CHECK_INTERVAL = 30 * 1000; // 30 seconds
const HEALTH_CHECK_TIMEOUT = 5000; // 5 seconds

/**
 * Service discovery middleware
 * Monitors service health and enables service routing
 */
function serviceDiscovery(services) {
  // Start periodic health checks
  startHealthChecks(services);

  return (req, res, next) => {
    // Add service discovery information to request
    req.services = services;
    req.serviceHealth = Object.fromEntries(serviceHealthCache);

    // Add service discovery headers
    res.set({
      'X-Gateway-Version': '2.0.0',
      'X-Services-Available': Object.keys(services).length,
      'X-Services-Healthy': getHealthyServicesCount()
    });

    next();
  };
}

/**
 * Start periodic health checks for all services
 */
function startHealthChecks(services) {
  // Initial health check
  checkAllServices(services);

  // Set up periodic health checks
  setInterval(() => {
    checkAllServices(services);
  }, HEALTH_CHECK_INTERVAL);

  logger.info(`Service health monitoring started for ${Object.keys(services).length} services`);
}

/**
 * Check health of all services
 */
async function checkAllServices(services) {
  const healthCheckPromises = Object.entries(services).map(([serviceName, serviceConfig]) =>
    checkServiceHealth(serviceName, serviceConfig)
  );

  await Promise.allSettled(healthCheckPromises);
}

/**
 * Check health of a single service
 */
async function checkServiceHealth(serviceName, serviceConfig) {
  const startTime = Date.now();

  try {
    const response = await axios.get(
      `${serviceConfig.url}${serviceConfig.healthPath}`,
      {
        timeout: HEALTH_CHECK_TIMEOUT,
        headers: {
          'User-Agent': 'AI-Trading-Gateway/2.0.0',
          'X-Health-Check': 'true'
        }
      }
    );

    const responseTime = Date.now() - startTime;
    const isHealthy = response.status === 200;

    const healthData = {
      status: isHealthy ? 'healthy' : 'unhealthy',
      responseTime,
      lastCheck: new Date().toISOString(),
      url: serviceConfig.url,
      statusCode: response.status,
      error: null
    };

    serviceHealthCache.set(serviceName, healthData);

    if (isHealthy) {
      logger.debug(`Service ${serviceName} is healthy (${responseTime}ms)`);
    } else {
      logger.warn(`Service ${serviceName} returned non-200 status: ${response.status}`);
    }

    return healthData;

  } catch (error) {
    const responseTime = Date.now() - startTime;
    const healthData = {
      status: 'unhealthy',
      responseTime,
      lastCheck: new Date().toISOString(),
      url: serviceConfig.url,
      statusCode: null,
      error: error.message
    };

    serviceHealthCache.set(serviceName, healthData);

    logger.warn(`Service ${serviceName} health check failed: ${error.message}`);
    return healthData;
  }
}

/**
 * Get count of healthy services
 */
function getHealthyServicesCount() {
  let healthyCount = 0;
  for (const health of serviceHealthCache.values()) {
    if (health.status === 'healthy') {
      healthyCount++;
    }
  }
  return healthyCount;
}

/**
 * Get service health status
 */
function getServiceHealth(serviceName) {
  return serviceHealthCache.get(serviceName) || {
    status: 'unknown',
    responseTime: null,
    lastCheck: null,
    error: 'No health data available'
  };
}

/**
 * Get all services health status
 */
function getAllServicesHealth() {
  const health = {};
  for (const [serviceName, healthData] of serviceHealthCache.entries()) {
    health[serviceName] = healthData;
  }
  return health;
}

/**
 * Check if a service is available for routing
 */
function isServiceAvailable(serviceName) {
  const health = serviceHealthCache.get(serviceName);
  return health && health.status === 'healthy';
}

/**
 * Get available services for a specific endpoint pattern
 */
function getAvailableServices(endpointPattern) {
  const availableServices = [];

  for (const [serviceName, health] of serviceHealthCache.entries()) {
    if (health.status === 'healthy') {
      // Check if service handles this endpoint pattern
      if (serviceHandlesEndpoint(serviceName, endpointPattern)) {
        availableServices.push(serviceName);
      }
    }
  }

  return availableServices;
}

/**
 * Check if a service handles a specific endpoint pattern
 */
function serviceHandlesEndpoint(serviceName, endpointPattern) {
  const serviceEndpointMap = {
    'user-management': ['/api/auth', '/api/users'],
    'subscription-service': ['/api/subscriptions'],
    'payment-gateway': ['/api/payments'],
    'notification-service': ['/api/notifications'],
    'billing-service': ['/api/billing'],
    'central-hub': ['/api/hub'],
    'data-bridge': ['/api/data'],
    'database-service': ['/api/database']
  };

  const endpoints = serviceEndpointMap[serviceName] || [];
  return endpoints.some(endpoint => endpointPattern.startsWith(endpoint));
}

/**
 * Get load balancing target for a service (future enhancement)
 */
function getLoadBalancedTarget(serviceName, services) {
  // For now, return the primary service URL
  // In future, this could implement round-robin, least-connections, etc.
  const serviceConfig = services[serviceName];
  if (!serviceConfig) {
    return null;
  }

  const health = getServiceHealth(serviceName);
  if (health.status !== 'healthy') {
    return null;
  }

  return serviceConfig.url;
}

/**
 * Service discovery stats for monitoring
 */
function getServiceDiscoveryStats() {
  const totalServices = serviceHealthCache.size;
  const healthyServices = getHealthyServicesCount();
  const unhealthyServices = totalServices - healthyServices;

  const stats = {
    totalServices,
    healthyServices,
    unhealthyServices,
    healthPercentage: totalServices > 0 ? Math.round((healthyServices / totalServices) * 100) : 0,
    lastUpdated: new Date().toISOString(),
    services: {}
  };

  // Add individual service stats
  for (const [serviceName, health] of serviceHealthCache.entries()) {
    stats.services[serviceName] = {
      status: health.status,
      responseTime: health.responseTime,
      lastCheck: health.lastCheck,
      uptime: calculateUptime(serviceName)
    };
  }

  return stats;
}

/**
 * Calculate service uptime percentage (simplified)
 */
function calculateUptime(serviceName) {
  // This is a simplified calculation
  // In production, you'd track this over time in a database
  const health = serviceHealthCache.get(serviceName);
  return health && health.status === 'healthy' ? 100 : 0;
}

/**
 * Circuit breaker pattern for service calls
 */
class ServiceCircuitBreaker {
  constructor(serviceName, options = {}) {
    this.serviceName = serviceName;
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000; // 1 minute
    this.monitoringPeriod = options.monitoringPeriod || 120000; // 2 minutes

    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.nextRetryTime = null;
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextRetryTime) {
        throw new Error(`Circuit breaker is OPEN for ${this.serviceName}`);
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
    this.nextRetryTime = null;
  }

  onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextRetryTime = Date.now() + this.resetTimeout;
      logger.warn(`Circuit breaker opened for ${this.serviceName}`);
    }
  }

  getState() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime,
      nextRetryTime: this.nextRetryTime
    };
  }
}

module.exports = {
  serviceDiscovery,
  getServiceHealth,
  getAllServicesHealth,
  isServiceAvailable,
  getAvailableServices,
  getLoadBalancedTarget,
  getServiceDiscoveryStats,
  ServiceCircuitBreaker
};