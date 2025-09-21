const express = require('express');
const axios = require('axios');
const logger = require('../utils/logger');
const config = require('../config/gateway.config');
const { metrics } = require('../middleware/metrics.middleware');

const router = express.Router();

// Simple health check
router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: '1.0.0'
  });
});

// Detailed health check with service dependencies
router.get('/detailed', async (req, res) => {
  const healthCheck = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: '1.0.0',
    services: {},
    system: {
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      platform: process.platform,
      nodeVersion: process.version
    }
  };

  // Check each service
  const serviceChecks = Object.entries(config.services).map(async ([serviceName, serviceConfig]) => {
    try {
      const startTime = Date.now();
      const response = await axios.get(`${serviceConfig.url}/health`, {
        timeout: 5000,
        validateStatus: () => true // Don't throw on non-2xx status
      });

      const responseTime = Date.now() - startTime;

      healthCheck.services[serviceName] = {
        status: response.status === 200 ? 'healthy' : 'unhealthy',
        url: serviceConfig.url,
        responseTime: `${responseTime}ms`,
        statusCode: response.status,
        lastChecked: new Date().toISOString()
      };

      if (response.status === 200 && response.data) {
        healthCheck.services[serviceName].details = response.data;
      }
    } catch (error) {
      healthCheck.services[serviceName] = {
        status: 'unhealthy',
        url: serviceConfig.url,
        error: error.message,
        lastChecked: new Date().toISOString()
      };

      // Update overall status if any critical service is down
      if (['auth', 'trading', 'market'].includes(serviceName)) {
        healthCheck.status = 'degraded';
      }
    }
  });

  await Promise.all(serviceChecks);

  // Check if any services are unhealthy
  const unhealthyServices = Object.values(healthCheck.services)
    .filter(service => service.status === 'unhealthy');

  if (unhealthyServices.length > 0) {
    healthCheck.status = 'degraded';
    healthCheck.issues = unhealthyServices.map(service => ({
      service: service.url,
      issue: service.error || 'Service unhealthy'
    }));
  }

  const statusCode = healthCheck.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthCheck);
});

// Readiness probe for Kubernetes
router.get('/ready', async (req, res) => {
  try {
    // Check critical services
    const criticalServices = ['auth', 'trading', 'market'];
    const checks = criticalServices.map(async (serviceName) => {
      const serviceConfig = config.services[serviceName];
      const response = await axios.get(`${serviceConfig.url}/health`, {
        timeout: 3000
      });
      return response.status === 200;
    });

    const results = await Promise.all(checks);
    const allHealthy = results.every(result => result === true);

    if (allHealthy) {
      res.json({
        status: 'ready',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        status: 'not ready',
        timestamp: new Date().toISOString(),
        message: 'Critical services are not available'
      });
    }
  } catch (error) {
    logger.error('Readiness check failed:', error);
    res.status(503).json({
      status: 'not ready',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

// Liveness probe for Kubernetes
router.get('/live', (req, res) => {
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Service-specific health checks
router.get('/services/:serviceName', async (req, res) => {
  const { serviceName } = req.params;
  const serviceConfig = config.services[serviceName];

  if (!serviceConfig) {
    return res.status(404).json({
      error: 'Service not found',
      availableServices: Object.keys(config.services)
    });
  }

  try {
    const startTime = Date.now();
    const response = await axios.get(`${serviceConfig.url}/health`, {
      timeout: 10000
    });

    const responseTime = Date.now() - startTime;

    res.json({
      service: serviceName,
      status: 'healthy',
      url: serviceConfig.url,
      responseTime: `${responseTime}ms`,
      statusCode: response.status,
      data: response.data,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Health check failed for ${serviceName}:`, error);
    res.status(503).json({
      service: serviceName,
      status: 'unhealthy',
      url: serviceConfig.url,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Metrics endpoint
router.get('/metrics', (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(`
# Gateway Health Metrics
gateway_uptime_seconds ${process.uptime()}
gateway_memory_usage_bytes ${process.memoryUsage().heapUsed}
gateway_memory_total_bytes ${process.memoryUsage().heapTotal}
gateway_cpu_usage_percent ${process.cpuUsage().user / 1000000}
gateway_version_info{version="1.0.0",environment="${process.env.NODE_ENV || 'development'}"} 1
  `);
});

module.exports = router;