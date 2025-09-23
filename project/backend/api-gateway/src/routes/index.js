/**
 * Main routing configuration for API Gateway
 * Handles health checks, status, and gateway-specific endpoints
 */

const express = require('express');
const router = express.Router();

/**
 * Health check endpoint
 */
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'api-gateway',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

/**
 * Gateway status endpoint with comprehensive information
 */
router.get('/status', async (req, res) => {
  try {
    const { getAllServices, getCriticalServices } = require('../config/services');

    const services = getAllServices();
    const criticalServices = getCriticalServices();

    res.json({
      service: 'API Gateway',
      status: 'operational',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      port: process.env.API_GATEWAY_PORT || 3001,
      environment: process.env.NODE_ENV || 'development',
      features: {
        authentication: true,
        rateLimiting: true,
        flowTracking: process.env.FLOW_TRACKING_ENABLED === 'true',
        chainDebugging: process.env.CHAIN_DEBUG_ENABLED === 'true',
        corsEnabled: true,
        compressionEnabled: true
      },
      services: {
        total: Object.keys(services).length,
        critical: Object.keys(criticalServices).length,
        configured: Object.keys(services)
      },
      performance: {
        uptime: `${Math.floor(process.uptime())}s`,
        memoryUsage: process.memoryUsage(),
        cpuUsage: process.cpuUsage()
      },
      configuration: {
        jwtEnabled: !!process.env.JWT_SECRET,
        rateLimitWindow: process.env.RATE_LIMIT_WINDOW_MS || '900000',
        maxRequests: process.env.RATE_LIMIT_MAX_REQUESTS || '100',
        corsOrigin: process.env.CORS_ORIGIN || '*',
        configServiceUrl: process.env.CONFIG_SERVICE_URL || 'http://localhost:8012'
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get gateway status',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Gateway metrics endpoint
 */
router.get('/metrics', async (req, res) => {
  try {
    const metrics = {
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      eventLoop: {
        delay: process.hrtime.bigint ? Number(process.hrtime.bigint()) : 0
      }
    };

    // Add rate limiting stats if available
    if (req.app.locals.rateLimitMiddleware) {
      try {
        metrics.rateLimit = await req.app.locals.rateLimitMiddleware.getStats();
      } catch (error) {
        metrics.rateLimit = { error: 'Failed to get rate limit stats' };
      }
    }

    // Add flow tracking stats if available
    if (req.app.locals.flowTrackingMiddleware) {
      try {
        metrics.flowTracking = await req.app.locals.flowTrackingMiddleware.getFlowStats();
      } catch (error) {
        metrics.flowTracking = { error: 'Failed to get flow tracking stats' };
      }
    }

    res.json(metrics);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get metrics',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Services configuration endpoint
 */
router.get('/services', (req, res) => {
  try {
    const { getAllServices, serviceCategories } = require('../config/services');

    const services = getAllServices();

    res.json({
      services,
      categories: serviceCategories,
      metadata: {
        totalServices: Object.keys(services).length,
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get services configuration',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Flow trace endpoint for debugging
 */
router.get('/flow/:flowId', async (req, res) => {
  try {
    const { flowId } = req.params;

    if (!flowId) {
      return res.status(400).json({
        error: 'Flow ID is required',
        timestamp: new Date().toISOString()
      });
    }

    let trace = [];

    // Get trace from flow tracking middleware if available
    if (req.app.locals.flowTrackingMiddleware) {
      trace = req.app.locals.flowTrackingMiddleware.getFlowTrace(flowId);
    }

    res.json({
      flowId,
      trace,
      metadata: {
        traceCount: trace.length,
        timestamp: new Date().toISOString(),
        note: 'This shows cached traces only. For complete flow history, check Flow Registry.'
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get flow trace',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Rate limit management endpoints (admin only)
 */
router.delete('/rate-limit/user/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'] || req.query.tenantId;

    if (!userId) {
      return res.status(400).json({
        error: 'User ID is required',
        timestamp: new Date().toISOString()
      });
    }

    if (req.app.locals.rateLimitMiddleware) {
      const result = await req.app.locals.rateLimitMiddleware.clearUserLimits(userId, tenantId);
      res.json({
        success: true,
        userId,
        tenantId,
        result,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Rate limiting not available',
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    res.status(500).json({
      error: 'Failed to clear rate limits',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

router.get('/rate-limit/user/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'] || req.query.tenantId;

    if (!userId) {
      return res.status(400).json({
        error: 'User ID is required',
        timestamp: new Date().toISOString()
      });
    }

    if (req.app.locals.rateLimitMiddleware) {
      const limits = await req.app.locals.rateLimitMiddleware.checkUserLimits(userId, tenantId);
      res.json({
        userId,
        tenantId,
        limits,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Rate limiting not available',
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    res.status(500).json({
      error: 'Failed to check rate limits',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Cache cleanup endpoint (admin only)
 */
router.post('/cleanup', async (req, res) => {
  try {
    const results = {};

    // Cleanup rate limiting cache
    if (req.app.locals.rateLimitMiddleware) {
      try {
        results.rateLimit = await req.app.locals.rateLimitMiddleware.cleanup();
      } catch (error) {
        results.rateLimit = { error: error.message };
      }
    }

    // Cleanup flow tracking cache
    if (req.app.locals.flowTrackingMiddleware) {
      try {
        results.flowTracking = req.app.locals.flowTrackingMiddleware.cleanupCache();
      } catch (error) {
        results.flowTracking = { error: error.message };
      }
    }

    res.json({
      success: true,
      cleanupResults: results,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      error: 'Cleanup failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Root endpoint
 */
router.get('/', (req, res) => {
  res.json({
    service: 'AI Trading Platform API Gateway',
    version: '1.0.0',
    description: 'Lightweight routing service with Flow Registry integration',
    documentation: 'https://docs.ai-trading-platform.com/api-gateway',
    endpoints: {
      health: '/health',
      status: '/status',
      metrics: '/metrics',
      services: '/services',
      flowTrace: '/flow/:flowId'
    },
    features: [
      'JWT Authentication',
      'Rate Limiting with DragonflyDB',
      'Flow Tracking & Tracing',
      'Error Handling with Impact Analysis',
      'Service Routing & Load Balancing',
      'CORS & Security Headers',
      'Request/Response Compression'
    ]
  });
});

module.exports = router;