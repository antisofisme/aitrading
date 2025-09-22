const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');
const winston = require('winston');
const redis = require('redis');
const jwt = require('jsonwebtoken');
require('dotenv').config();

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const multiTenantAuth = require('./middleware/multiTenantAuth');
const multiTenantRateLimit = require('./middleware/multiTenantRateLimit');
const serviceDiscovery = require('./middleware/serviceDiscovery');
const requestLogging = require('./middleware/requestLogging');
const healthCheck = require('./routes/enhanced-health');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'api-gateway-enhanced' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();
const PORT = process.env.PORT || 8000;

// Initialize Redis client for multi-tenant rate limiting
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD,
  retry_strategy: (options) => {
    if (options.error && options.error.code === 'ECONNREFUSED') {
      logger.error('Redis connection refused');
      return new Error('Redis connection refused');
    }
    if (options.total_retry_time > 1000 * 60 * 60) {
      logger.error('Redis retry time exhausted');
      return new Error('Retry time exhausted');
    }
    if (options.attempt > 10) {
      logger.error('Max Redis connection attempts reached');
      return undefined;
    }
    return Math.min(options.attempt * 100, 3000);
  }
});

// Service registry configuration
const SERVICES = {
  'user-management': {
    url: process.env.USER_MANAGEMENT_URL || 'http://localhost:8021',
    healthPath: '/health',
    timeout: 30000
  },
  'subscription-service': {
    url: process.env.SUBSCRIPTION_SERVICE_URL || 'http://localhost:8022',
    healthPath: '/health',
    timeout: 30000
  },
  'payment-gateway': {
    url: process.env.PAYMENT_GATEWAY_URL || 'http://localhost:8023',
    healthPath: '/health',
    timeout: 30000
  },
  'notification-service': {
    url: process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:8024',
    healthPath: '/health',
    timeout: 30000
  },
  'billing-service': {
    url: process.env.BILLING_SERVICE_URL || 'http://localhost:8025',
    healthPath: '/health',
    timeout: 30000
  },
  'central-hub': {
    url: process.env.CENTRAL_HUB_URL || 'http://localhost:7000',
    healthPath: '/health',
    timeout: 30000
  },
  'data-bridge': {
    url: process.env.DATA_BRIDGE_URL || 'http://localhost:8001',
    healthPath: '/health',
    timeout: 30000
  },
  'database-service': {
    url: process.env.DATABASE_SERVICE_URL || 'http://localhost:8006',
    healthPath: '/health',
    timeout: 30000
  }
};

// Trust proxy for rate limiting behind load balancer
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// CORS with multi-tenant support
app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);

    const allowedOrigins = process.env.CORS_ORIGINS ?
      process.env.CORS_ORIGINS.split(',') :
      ['http://localhost:3000', 'http://localhost:3001'];

    // Add tenant-specific origins
    const tenantOrigins = [
      'https://app.aitrading.com',
      'https://dashboard.aitrading.com',
      'https://admin.aitrading.com'
    ];

    const allAllowedOrigins = [...allowedOrigins, ...tenantOrigins];

    if (allAllowedOrigins.includes(origin)) {
      return callback(null, true);
    }

    logger.warn(`Blocked CORS request from origin: ${origin}`);
    return callback(new Error('Not allowed by CORS'), false);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-API-Key',
    'X-User-ID',
    'X-Tenant-ID',
    'X-Client-Version',
    'X-Request-ID'
  ]
}));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(compression());

// Request logging with correlation ID
app.use(requestLogging);

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', {
    stream: { write: message => logger.info(message.trim()) }
  }));
}

// Global rate limiting (before authentication)
const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Global limit per IP
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: '15 minutes'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use(globalLimiter);

// Health check (no auth required)
app.use('/health', healthCheck);

// Service discovery middleware
app.use(serviceDiscovery(SERVICES));

// Multi-tenant authentication (extracts user and tenant info)
app.use(multiTenantAuth);

// Multi-tenant rate limiting (per user/tenant)
app.use(multiTenantRateLimit(redisClient));

// Root endpoint with enhanced information
app.get('/', (req, res) => {
  res.json({
    service: 'AI Trading Platform - Enhanced API Gateway',
    version: '2.0.0',
    status: 'operational',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    features: {
      multiTenant: 'enabled',
      serviceDiscovery: 'enabled',
      loadBalancing: 'enabled',
      rateLimiting: 'per-user',
      authentication: 'jwt-multi-tenant',
      monitoring: 'enabled'
    },
    services: Object.keys(SERVICES),
    endpoints: {
      auth: '/api/auth',
      users: '/api/users',
      subscriptions: '/api/subscriptions',
      payments: '/api/payments',
      notifications: '/api/notifications',
      billing: '/api/billing',
      health: '/health',
      metrics: '/metrics'
    },
    documentation: '/docs'
  });
});

// User Management Service Proxy
app.use('/api/auth', createProxyMiddleware({
  target: SERVICES['user-management'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/auth': '/api/auth'
  },
  timeout: SERVICES['user-management'].timeout,
  onError: (err, req, res) => {
    logger.error(`User Management Service error: ${err.message}`);
    res.status(503).json({
      success: false,
      error: 'Service temporarily unavailable',
      service: 'user-management',
      message: 'Please try again later'
    });
  },
  onProxyReq: (proxyReq, req, res) => {
    // Add service-to-service authentication
    const serviceToken = generateServiceToken('api-gateway', 'user-management');
    proxyReq.setHeader('X-Service-Token', serviceToken);

    // Forward user context
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

app.use('/api/users', createProxyMiddleware({
  target: SERVICES['user-management'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/users': '/api/users'
  },
  timeout: SERVICES['user-management'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'user-management');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Subscription Service Proxy
app.use('/api/subscriptions', createProxyMiddleware({
  target: SERVICES['subscription-service'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/subscriptions': '/api/subscriptions'
  },
  timeout: SERVICES['subscription-service'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'subscription-service');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Payment Gateway Proxy
app.use('/api/payments', createProxyMiddleware({
  target: SERVICES['payment-gateway'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/payments': '/api/payments'
  },
  timeout: SERVICES['payment-gateway'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'payment-gateway');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Notification Service Proxy
app.use('/api/notifications', createProxyMiddleware({
  target: SERVICES['notification-service'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/notifications': '/api/notifications'
  },
  timeout: SERVICES['notification-service'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'notification-service');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Billing Service Proxy
app.use('/api/billing', createProxyMiddleware({
  target: SERVICES['billing-service'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/billing': '/api/billing'
  },
  timeout: SERVICES['billing-service'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'billing-service');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Central Hub Proxy (for coordination)
app.use('/api/hub', createProxyMiddleware({
  target: SERVICES['central-hub'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/hub': '/api'
  },
  timeout: SERVICES['central-hub'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'central-hub');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Data Bridge Proxy (for trading data)
app.use('/api/data', createProxyMiddleware({
  target: SERVICES['data-bridge'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/data': '/api'
  },
  timeout: SERVICES['data-bridge'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'data-bridge');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Database Service Proxy (admin only)
app.use('/api/database', (req, res, next) => {
  // Only allow enterprise tier or admin users
  if (!req.user || (req.user.subscription !== 'ENTERPRISE' && req.user.role !== 'admin')) {
    return res.status(403).json({
      success: false,
      error: 'Access denied',
      message: 'Database access requires ENTERPRISE subscription or admin privileges'
    });
  }
  next();
}, createProxyMiddleware({
  target: SERVICES['database-service'].url,
  changeOrigin: true,
  pathRewrite: {
    '^/api/database': '/api'
  },
  timeout: SERVICES['database-service'].timeout,
  onProxyReq: (proxyReq, req, res) => {
    const serviceToken = generateServiceToken('api-gateway', 'database-service');
    proxyReq.setHeader('X-Service-Token', serviceToken);
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Tier', req.user.subscription);
    }
  }
}));

// Metrics endpoint (admin only)
app.get('/metrics', (req, res) => {
  if (!req.user || (req.user.subscription !== 'ENTERPRISE' && req.user.role !== 'admin')) {
    return res.status(403).json({
      success: false,
      error: 'Access denied',
      message: 'Metrics access requires ENTERPRISE subscription or admin privileges'
    });
  }

  // Return gateway metrics
  res.json({
    timestamp: new Date().toISOString(),
    gateway: {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage()
    },
    services: SERVICES,
    rateLimiting: {
      redis: redisClient.connected,
      activeConnections: redisClient.command_queue_length || 0
    }
  });
});

// Service health aggregation endpoint
app.get('/health/services', async (req, res) => {
  const healthChecks = {};

  for (const [serviceName, serviceConfig] of Object.entries(SERVICES)) {
    try {
      const response = await fetch(`${serviceConfig.url}${serviceConfig.healthPath}`, {
        timeout: 5000
      });

      if (response.ok) {
        healthChecks[serviceName] = {
          status: 'healthy',
          url: serviceConfig.url,
          responseTime: `${Date.now() - Date.now()}ms`
        };
      } else {
        healthChecks[serviceName] = {
          status: 'unhealthy',
          url: serviceConfig.url,
          error: `HTTP ${response.status}`
        };
      }
    } catch (error) {
      healthChecks[serviceName] = {
        status: 'unreachable',
        url: serviceConfig.url,
        error: error.message
      };
    }
  }

  const allHealthy = Object.values(healthChecks).every(check => check.status === 'healthy');

  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    services: healthChecks
  });
});

// Generate service-to-service authentication token
function generateServiceToken(fromService, toService) {
  const payload = {
    iss: fromService,
    aud: toService,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 300, // 5 minute expiry
    type: 'service'
  };

  return jwt.sign(payload, process.env.SERVICE_SECRET || 'service-secret-key');
}

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    message: `The endpoint ${req.method} ${req.originalUrl} does not exist`,
    suggestion: 'Check the API documentation at /',
    availableServices: Object.keys(SERVICES)
  });
});

// Error handling middleware
app.use(errorHandler);

// Initialize and start server
async function startServer() {
  try {
    logger.info('Initializing Enhanced API Gateway...');

    // Test Redis connection
    try {
      await redisClient.ping();
      logger.info('Redis connection established');
    } catch (error) {
      logger.warn('Redis connection failed, rate limiting will use memory fallback');
    }

    // Start server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Enhanced API Gateway running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Multi-tenant support: enabled`);
      logger.info(`Service discovery: enabled`);
      logger.info(`Health check: http://localhost:${PORT}/health`);
      logger.info(`Services health: http://localhost:${PORT}/health/services`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM received, shutting down gracefully');
      server.close(() => {
        redisClient.quit(() => {
          logger.info('Process terminated');
          process.exit(0);
        });
      });
    });

    process.on('SIGINT', () => {
      logger.info('SIGINT received, shutting down gracefully');
      server.close(() => {
        redisClient.quit(() => {
          logger.info('Process terminated');
          process.exit(0);
        });
      });
    });

    return server;
  } catch (error) {
    logger.error('Failed to start Enhanced API Gateway:', error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer, SERVICES };