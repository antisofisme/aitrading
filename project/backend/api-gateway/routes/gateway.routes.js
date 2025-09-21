const express = require('express');
const logger = require('../utils/logger');
const authMiddleware = require('../middleware/auth.middleware');
const { metrics } = require('../middleware/metrics.middleware');
const ServiceRegistry = require('../utils/service-registry');

const router = express.Router();
const serviceRegistry = new ServiceRegistry();

// Gateway information endpoint
router.get('/info', (req, res) => {
  res.json({
    name: 'AI Trading Platform API Gateway',
    version: '1.0.0',
    description: 'Central API Gateway for microservices routing and management',
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    features: [
      'Authentication & Authorization',
      'Rate Limiting',
      'Request/Response Logging',
      'Service Discovery',
      'Health Monitoring',
      'Metrics Collection',
      'CORS Handling',
      'Error Management'
    ],
    endpoints: {
      health: '/health',
      metrics: '/metrics',
      serviceRegistry: '/gateway/services',
      documentation: '/api/docs'
    },
    timestamp: new Date().toISOString()
  });
});

// Service registry endpoints
router.get('/services', authMiddleware.adminOnly, async (req, res) => {
  try {
    const services = await serviceRegistry.getAllServices();
    res.json({
      services,
      count: Object.keys(services).length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Failed to get services:', error);
    res.status(500).json({
      error: 'Failed to retrieve services',
      message: error.message
    });
  }
});

// Register a new service
router.post('/services', authMiddleware.adminOnly, async (req, res) => {
  try {
    const { name, url, health, version, metadata } = req.body;

    if (!name || !url) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['name', 'url']
      });
    }

    const service = await serviceRegistry.register({
      name,
      url,
      health: health || `${url}/health`,
      version: version || '1.0.0',
      metadata: metadata || {},
      registeredAt: new Date().toISOString(),
      registeredBy: req.auth.user.id
    });

    logger.info(`Service registered: ${name} at ${url}`);
    res.status(201).json({
      message: 'Service registered successfully',
      service
    });
  } catch (error) {
    logger.error('Failed to register service:', error);
    res.status(500).json({
      error: 'Failed to register service',
      message: error.message
    });
  }
});

// Update service information
router.put('/services/:serviceName', authMiddleware.adminOnly, async (req, res) => {
  try {
    const { serviceName } = req.params;
    const updates = req.body;

    const service = await serviceRegistry.update(serviceName, {
      ...updates,
      updatedAt: new Date().toISOString(),
      updatedBy: req.auth.user.id
    });

    if (!service) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName
      });
    }

    logger.info(`Service updated: ${serviceName}`);
    res.json({
      message: 'Service updated successfully',
      service
    });
  } catch (error) {
    logger.error('Failed to update service:', error);
    res.status(500).json({
      error: 'Failed to update service',
      message: error.message
    });
  }
});

// Unregister a service
router.delete('/services/:serviceName', authMiddleware.adminOnly, async (req, res) => {
  try {
    const { serviceName } = req.params;

    const success = await serviceRegistry.unregister(serviceName);

    if (!success) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName
      });
    }

    logger.info(`Service unregistered: ${serviceName}`);
    res.json({
      message: 'Service unregistered successfully',
      serviceName
    });
  } catch (error) {
    logger.error('Failed to unregister service:', error);
    res.status(500).json({
      error: 'Failed to unregister service',
      message: error.message
    });
  }
});

// Get service health status
router.get('/services/:serviceName/health', authMiddleware.adminOnly, async (req, res) => {
  try {
    const { serviceName } = req.params;
    const health = await serviceRegistry.checkHealth(serviceName);

    if (!health) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName
      });
    }

    res.json(health);
  } catch (error) {
    logger.error('Failed to check service health:', error);
    res.status(500).json({
      error: 'Failed to check service health',
      message: error.message
    });
  }
});

// Gateway statistics
router.get('/stats', authMiddleware.adminOnly, async (req, res) => {
  try {
    const services = await serviceRegistry.getAllServices();
    const healthyServices = Object.values(services).filter(s => s.status === 'healthy').length;
    const unhealthyServices = Object.values(services).filter(s => s.status !== 'healthy').length;

    res.json({
      gateway: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        cpu: process.cpuUsage(),
        platform: process.platform,
        nodeVersion: process.version
      },
      services: {
        total: Object.keys(services).length,
        healthy: healthyServices,
        unhealthy: unhealthyServices,
        list: Object.keys(services)
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Failed to get gateway stats:', error);
    res.status(500).json({
      error: 'Failed to get gateway statistics',
      message: error.message
    });
  }
});

// Configuration endpoint
router.get('/config', authMiddleware.adminOnly, (req, res) => {
  const config = require('../config/gateway.config');

  // Remove sensitive information
  const safeConfig = {
    server: {
      port: config.server.port,
      host: config.server.host,
      environment: config.server.environment
    },
    rateLimit: config.rateLimit,
    cors: config.cors,
    services: Object.keys(config.services).reduce((acc, key) => {
      acc[key] = {
        url: config.services[key].url,
        timeout: config.services[key].timeout
      };
      return acc;
    }, {}),
    monitoring: config.monitoring
  };

  res.json(safeConfig);
});

// Force service health check
router.post('/services/:serviceName/health-check', authMiddleware.adminOnly, async (req, res) => {
  try {
    const { serviceName } = req.params;
    const health = await serviceRegistry.forceHealthCheck(serviceName);

    if (!health) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName
      });
    }

    res.json({
      message: 'Health check completed',
      serviceName,
      health
    });
  } catch (error) {
    logger.error('Failed to force health check:', error);
    res.status(500).json({
      error: 'Failed to force health check',
      message: error.message
    });
  }
});

// Metrics endpoint (Prometheus format)
router.get('/metrics', (req, res) => {
  metrics.getMetrics().then(metrics => {
    res.set('Content-Type', 'text/plain');
    res.send(metrics);
  }).catch(error => {
    logger.error('Failed to get metrics:', error);
    res.status(500).send('Failed to get metrics');
  });
});

// Request tracing endpoint
router.get('/trace/:requestId', authMiddleware.adminOnly, (req, res) => {
  const { requestId } = req.params;

  // This would typically query a distributed tracing system
  // For now, return a placeholder response
  res.json({
    requestId,
    message: 'Request tracing not implemented yet',
    suggestion: 'Integrate with Jaeger or Zipkin for distributed tracing'
  });
});

module.exports = router;