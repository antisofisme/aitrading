/**
 * Service Routing for API Gateway
 * Handles proxying requests to all microservices with health monitoring
 */

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');
const winston = require('winston');
const { getService, getAllServices, getServiceByPrefix } = require('../config/services');

const router = express.Router();

class ServiceRouter {
  constructor(logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()]
    });

    this.serviceHealth = new Map();
    this.setupHealthMonitoring();
  }

  /**
   * Setup health monitoring for all services
   */
  setupHealthMonitoring() {
    const services = getAllServices();

    // Initialize health status
    Object.keys(services).forEach(serviceName => {
      this.serviceHealth.set(serviceName, {
        status: 'unknown',
        lastChecked: null,
        consecutiveFailures: 0,
        responseTime: null
      });
    });

    // Start periodic health checks
    this.startHealthChecks();
  }

  /**
   * Start periodic health checks
   */
  startHealthChecks() {
    const checkInterval = parseInt(process.env.HEALTH_CHECK_INTERVAL_MS) || 30000;

    setInterval(async () => {
      await this.performHealthChecks();
    }, checkInterval);

    // Initial health check
    setTimeout(() => this.performHealthChecks(), 5000);
  }

  /**
   * Perform health checks on all services
   */
  async performHealthChecks() {
    const services = getAllServices();

    const healthPromises = Object.entries(services).map(async ([serviceName, config]) => {
      try {
        const startTime = Date.now();

        const response = await axios.get(
          `${config.baseUrl}${config.healthEndpoint}`,
          {
            timeout: 5000,
            validateStatus: (status) => status < 500
          }
        );

        const responseTime = Date.now() - startTime;
        const isHealthy = response.status === 200;

        this.serviceHealth.set(serviceName, {
          status: isHealthy ? 'healthy' : 'unhealthy',
          lastChecked: new Date().toISOString(),
          consecutiveFailures: isHealthy ? 0 : this.serviceHealth.get(serviceName)?.consecutiveFailures + 1 || 1,
          responseTime,
          statusCode: response.status
        });

        if (!isHealthy) {
          this.logger.warn('Service health check failed', {
            serviceName,
            statusCode: response.status,
            responseTime,
            url: `${config.baseUrl}${config.healthEndpoint}`
          });
        }

      } catch (error) {
        const health = this.serviceHealth.get(serviceName) || {};
        this.serviceHealth.set(serviceName, {
          status: 'unhealthy',
          lastChecked: new Date().toISOString(),
          consecutiveFailures: (health.consecutiveFailures || 0) + 1,
          responseTime: null,
          error: error.message
        });

        this.logger.error('Service health check error', {
          serviceName,
          error: error.message,
          consecutiveFailures: this.serviceHealth.get(serviceName).consecutiveFailures
        });
      }
    });

    await Promise.allSettled(healthPromises);
  }

  /**
   * Check if service is healthy
   */
  isServiceHealthy(serviceName) {
    const health = this.serviceHealth.get(serviceName);
    return health && health.status === 'healthy';
  }

  /**
   * Get service health status
   */
  getServiceHealth(serviceName) {
    return this.serviceHealth.get(serviceName) || {
      status: 'unknown',
      lastChecked: null,
      consecutiveFailures: 0,
      responseTime: null
    };
  }

  /**
   * Create proxy middleware for a service
   */
  createServiceProxy(serviceName, serviceConfig) {
    return createProxyMiddleware({
      target: serviceConfig.baseUrl,
      changeOrigin: true,
      pathRewrite: (path) => {
        // Remove service prefix from path
        return path.replace(serviceConfig.prefix, '');
      },
      timeout: serviceConfig.timeout || 30000,
      proxyTimeout: serviceConfig.timeout || 30000,

      // Add flow tracking headers
      onProxyReq: (proxyReq, req, res) => {
        // Add flow tracking headers
        if (req.app.locals.flowTrackingMiddleware) {
          const headers = req.app.locals.flowTrackingMiddleware.createDownstreamHeaders(req, serviceName);
          Object.entries(headers).forEach(([key, value]) => {
            proxyReq.setHeader(key, value);
          });
        }

        // Track downstream call start time
        req.downstreamStartTime = Date.now();

        this.logger.info('Proxying request to service', {
          serviceName,
          targetUrl: `${serviceConfig.baseUrl}${proxyReq.path}`,
          method: req.method,
          flowId: req.flowId,
          requestId: req.requestId,
          userId: req.user?.id
        });
      },

      onProxyRes: (proxyRes, req, res) => {
        // Track downstream call completion
        if (req.downstreamStartTime && req.app.locals.flowTrackingMiddleware) {
          req.app.locals.flowTrackingMiddleware.trackDownstreamCall(
            req,
            serviceName,
            `${serviceConfig.baseUrl}${req.path}`,
            req.downstreamStartTime
          ).catch(error => {
            this.logger.debug('Failed to track downstream call', {
              error: error.message,
              serviceName,
              flowId: req.flowId
            });
          });
        }

        this.logger.info('Received response from service', {
          serviceName,
          statusCode: proxyRes.statusCode,
          duration: req.downstreamStartTime ? `${Date.now() - req.downstreamStartTime}ms` : 'unknown',
          flowId: req.flowId,
          requestId: req.requestId
        });
      },

      onError: (err, req, res) => {
        this.logger.error('Proxy error', {
          serviceName,
          error: err.message,
          target: serviceConfig.baseUrl,
          flowId: req.flowId,
          requestId: req.requestId
        });

        // Update service health on error
        const health = this.serviceHealth.get(serviceName) || {};
        this.serviceHealth.set(serviceName, {
          ...health,
          status: 'unhealthy',
          lastChecked: new Date().toISOString(),
          consecutiveFailures: (health.consecutiveFailures || 0) + 1,
          error: err.message
        });

        if (!res.headersSent) {
          res.status(503).json({
            error: 'Service unavailable',
            message: `${serviceName} is currently unavailable`,
            code: 'SERVICE_UNAVAILABLE',
            serviceName,
            retryAfter: 30,
            timestamp: new Date().toISOString()
          });
        }
      }
    });
  }

  /**
   * Setup all service routes
   */
  setupRoutes() {
    const services = getAllServices();

    Object.entries(services).forEach(([serviceName, serviceConfig]) => {
      // Health check middleware before proxying
      router.use(serviceConfig.prefix, (req, res, next) => {
        if (!this.isServiceHealthy(serviceName)) {
          const health = this.getServiceHealth(serviceName);

          this.logger.warn('Request to unhealthy service', {
            serviceName,
            path: req.path,
            method: req.method,
            health,
            flowId: req.flowId,
            requestId: req.requestId
          });

          // Allow health check requests to pass through
          if (req.path === serviceConfig.healthEndpoint) {
            return next();
          }

          // Return service unavailable for other requests
          return res.status(503).json({
            error: 'Service temporarily unavailable',
            message: `${serviceConfig.name} is currently unhealthy`,
            code: 'SERVICE_UNHEALTHY',
            serviceName,
            health: {
              status: health.status,
              consecutiveFailures: health.consecutiveFailures,
              lastChecked: health.lastChecked
            },
            retryAfter: 30,
            timestamp: new Date().toISOString()
          });
        }

        next();
      });

      // Create and mount proxy middleware
      const proxy = this.createServiceProxy(serviceName, serviceConfig);
      router.use(serviceConfig.prefix, proxy);

      this.logger.info('Service route configured', {
        serviceName,
        prefix: serviceConfig.prefix,
        target: serviceConfig.baseUrl,
        critical: serviceConfig.critical
      });
    });

    return router;
  }

  /**
   * Get overall health summary
   */
  getHealthSummary() {
    const services = getAllServices();
    const summary = {
      totalServices: Object.keys(services).length,
      healthyServices: 0,
      unhealthyServices: 0,
      unknownServices: 0,
      criticalServicesDown: 0,
      services: {}
    };

    Object.entries(services).forEach(([serviceName, config]) => {
      const health = this.getServiceHealth(serviceName);
      summary.services[serviceName] = {
        ...health,
        critical: config.critical,
        name: config.name
      };

      switch (health.status) {
        case 'healthy':
          summary.healthyServices++;
          break;
        case 'unhealthy':
          summary.unhealthyServices++;
          if (config.critical) {
            summary.criticalServicesDown++;
          }
          break;
        default:
          summary.unknownServices++;
      }
    });

    summary.overallStatus = summary.criticalServicesDown > 0 ? 'critical' :
                          summary.unhealthyServices > 0 ? 'degraded' : 'healthy';

    return summary;
  }
}

// Create service router instance
const serviceRouter = new ServiceRouter();

// Health summary endpoint
router.get('/health-summary', (req, res) => {
  try {
    const summary = serviceRouter.getHealthSummary();
    res.json({
      ...summary,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get health summary',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Individual service health endpoint
router.get('/health/:serviceName', (req, res) => {
  try {
    const { serviceName } = req.params;
    const service = getService(serviceName);

    if (!service) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName,
        timestamp: new Date().toISOString()
      });
    }

    const health = serviceRouter.getServiceHealth(serviceName);

    res.json({
      serviceName,
      service: service.name,
      health,
      config: {
        baseUrl: service.baseUrl,
        critical: service.critical,
        timeout: service.timeout
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get service health',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Force health check for a specific service
router.post('/health/:serviceName/check', async (req, res) => {
  try {
    const { serviceName } = req.params;
    const service = getService(serviceName);

    if (!service) {
      return res.status(404).json({
        error: 'Service not found',
        serviceName,
        timestamp: new Date().toISOString()
      });
    }

    // Perform immediate health check
    const startTime = Date.now();

    try {
      const response = await axios.get(
        `${service.baseUrl}${service.healthEndpoint}`,
        { timeout: 5000 }
      );

      const responseTime = Date.now() - startTime;
      const isHealthy = response.status === 200;

      serviceRouter.serviceHealth.set(serviceName, {
        status: isHealthy ? 'healthy' : 'unhealthy',
        lastChecked: new Date().toISOString(),
        consecutiveFailures: isHealthy ? 0 : serviceRouter.serviceHealth.get(serviceName)?.consecutiveFailures + 1 || 1,
        responseTime,
        statusCode: response.status
      });

      res.json({
        serviceName,
        health: serviceRouter.getServiceHealth(serviceName),
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      const health = serviceRouter.serviceHealth.get(serviceName) || {};
      serviceRouter.serviceHealth.set(serviceName, {
        status: 'unhealthy',
        lastChecked: new Date().toISOString(),
        consecutiveFailures: (health.consecutiveFailures || 0) + 1,
        responseTime: null,
        error: error.message
      });

      res.json({
        serviceName,
        health: serviceRouter.getServiceHealth(serviceName),
        timestamp: new Date().toISOString()
      });
    }

  } catch (error) {
    res.status(500).json({
      error: 'Failed to check service health',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Setup all service routes
serviceRouter.setupRoutes();

module.exports = router;