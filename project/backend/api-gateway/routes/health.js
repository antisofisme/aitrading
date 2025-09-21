const express = require('express');
const axios = require('axios');
const config = require('../config/config');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * Health check endpoints for API Gateway
 */

// Basic health check
router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'api-gateway',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: config.environment
  });
});

// Detailed health check including dependent services
router.get('/detailed', async (req, res) => {
  const healthChecks = {
    gateway: {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage()
    },
    services: {}
  };

  // Check each registered service
  const serviceChecks = Object.entries(config.services).map(async ([serviceName, serviceConfig]) => {
    try {
      const startTime = Date.now();
      const response = await axios.get(
        `${serviceConfig.url}${serviceConfig.healthPath || '/health'}`,
        { timeout: 5000 }
      );

      const responseTime = Date.now() - startTime;

      healthChecks.services[serviceName] = {
        status: 'healthy',
        url: serviceConfig.url,
        responseTime: `${responseTime}ms`,
        timestamp: new Date().toISOString(),
        data: response.data
      };
    } catch (error) {
      healthChecks.services[serviceName] = {
        status: 'unhealthy',
        url: serviceConfig.url,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  });

  // Wait for all service checks to complete
  await Promise.all(serviceChecks);

  // Determine overall health status
  const allServicesHealthy = Object.values(healthChecks.services)
    .every(service => service.status === 'healthy');

  const overallStatus = allServicesHealthy ? 'healthy' : 'degraded';

  res.status(overallStatus === 'healthy' ? 200 : 503).json({
    status: overallStatus,
    ...healthChecks
  });
});

// Readiness probe
router.get('/ready', async (req, res) => {
  try {
    // Check if essential services are available
    const essentialServices = ['hub']; // Central Hub is essential for Phase 1

    const readinessChecks = await Promise.all(
      essentialServices.map(async (serviceName) => {
        const serviceConfig = config.services[serviceName];
        if (!serviceConfig) return { [serviceName]: false };

        try {
          await axios.get(
            `${serviceConfig.url}${serviceConfig.healthPath || '/health'}`,
            { timeout: 3000 }
          );
          return { [serviceName]: true };
        } catch (error) {
          return { [serviceName]: false };
        }
      })
    );

    const readinessStatus = readinessChecks.reduce((acc, check) => ({ ...acc, ...check }), {});
    const isReady = Object.values(readinessStatus).every(Boolean);

    res.status(isReady ? 200 : 503).json({
      ready: isReady,
      services: readinessStatus,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Readiness check failed:', error);
    res.status(503).json({
      ready: false,
      error: 'Readiness check failed',
      timestamp: new Date().toISOString()
    });
  }
});

// Liveness probe
router.get('/live', (req, res) => {
  // Simple liveness check - if this endpoint responds, the service is alive
  res.json({
    alive: true,
    timestamp: new Date().toISOString(),
    pid: process.pid
  });
});

// Metrics endpoint for monitoring
router.get('/metrics', (req, res) => {
  const metrics = {
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cpu: process.cpuUsage(),
    platform: process.platform,
    nodeVersion: process.version,
    environment: config.environment,
    registeredServices: Object.keys(config.services).length
  };

  res.json(metrics);
});

module.exports = router;