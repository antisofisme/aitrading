/**
 * Flow Registry Middleware
 *
 * Authentication, logging, rate limiting, and security middleware
 * for Flow Registry API endpoints
 */

const jwt = require('jsonwebtoken');
const winston = require('winston');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');

// Initialize logger for middleware
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/flow-middleware.log' })
  ]
});

/**
 * Request ID middleware - Add unique request ID for tracing
 */
const requestId = (req, res, next) => {
  req.requestId = req.headers['x-request-id'] || uuidv4();
  res.setHeader('x-request-id', req.requestId);
  next();
};

/**
 * Request logging middleware
 */
const requestLogger = (req, res, next) => {
  const startTime = Date.now();

  // Log request start
  logger.info('Request started', {
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    userAgent: req.headers['user-agent'],
    ip: req.ip || req.connection.remoteAddress,
    body: req.method === 'POST' || req.method === 'PUT' ? req.body : undefined
  });

  // Override res.json to log response
  const originalJson = res.json;
  res.json = function(...args) {
    const duration = Date.now() - startTime;

    logger.info('Request completed', {
      requestId: req.requestId,
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: duration,
      responseSize: JSON.stringify(args[0]).length
    });

    return originalJson.apply(this, args);
  };

  next();
};

/**
 * Authentication middleware - Verify JWT tokens
 */
const authenticate = (options = {}) => {
  const { required = true, allowServiceTokens = true } = options;

  return (req, res, next) => {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      if (!required) {
        req.user = null;
        return next();
      }

      return res.status(401).json({
        error: 'Authentication Required',
        message: 'Bearer token is required',
        requestId: req.requestId
      });
    }

    try {
      // Verify JWT token
      const jwtSecret = process.env.JWT_SECRET || 'your-secret-key';
      const decoded = jwt.verify(token, jwtSecret);

      // Check if it's a service token
      if (allowServiceTokens && decoded.type === 'service') {
        req.user = {
          id: decoded.service,
          type: 'service',
          permissions: decoded.permissions || [],
          service: decoded.service
        };
      } else {
        // Regular user token
        req.user = {
          id: decoded.userId || decoded.sub,
          username: decoded.username,
          email: decoded.email,
          type: 'user',
          permissions: decoded.permissions || [],
          roles: decoded.roles || []
        };
      }

      // Add user info to request context
      req.userContext = {
        userId: req.user.id,
        userType: req.user.type,
        permissions: req.user.permissions,
        authenticatedAt: new Date()
      };

      logger.debug('User authenticated', {
        requestId: req.requestId,
        userId: req.user.id,
        userType: req.user.type
      });

      next();
    } catch (error) {
      logger.warn('Authentication failed', {
        requestId: req.requestId,
        error: error.message,
        token: token?.substring(0, 20) + '...'
      });

      if (error.name === 'TokenExpiredError') {
        return res.status(401).json({
          error: 'Token Expired',
          message: 'The provided token has expired',
          requestId: req.requestId
        });
      }

      if (error.name === 'JsonWebTokenError') {
        return res.status(401).json({
          error: 'Invalid Token',
          message: 'The provided token is invalid',
          requestId: req.requestId
        });
      }

      return res.status(401).json({
        error: 'Authentication Failed',
        message: 'Token verification failed',
        requestId: req.requestId
      });
    }
  };
};

/**
 * Authorization middleware - Check permissions
 */
const authorize = (requiredPermissions = []) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication Required',
        message: 'User must be authenticated to access this resource',
        requestId: req.requestId
      });
    }

    // Service tokens have elevated permissions
    if (req.user.type === 'service') {
      return next();
    }

    // Check if user has required permissions
    const userPermissions = req.user.permissions || [];
    const hasPermission = requiredPermissions.every(permission =>
      userPermissions.includes(permission) || userPermissions.includes('admin')
    );

    if (!hasPermission) {
      logger.warn('Authorization failed', {
        requestId: req.requestId,
        userId: req.user.id,
        requiredPermissions,
        userPermissions
      });

      return res.status(403).json({
        error: 'Insufficient Permissions',
        message: `Required permissions: ${requiredPermissions.join(', ')}`,
        requestId: req.requestId
      });
    }

    logger.debug('User authorized', {
      requestId: req.requestId,
      userId: req.user.id,
      permissions: requiredPermissions
    });

    next();
  };
};

/**
 * Rate limiting middleware
 */
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too Many Requests',
    message: 'Rate limit exceeded. Please try again later.',
  },
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    logger.warn('Rate limit exceeded', {
      requestId: req.requestId,
      ip: req.ip,
      userAgent: req.headers['user-agent']
    });

    res.status(429).json({
      error: 'Too Many Requests',
      message: 'Rate limit exceeded. Please try again later.',
      requestId: req.requestId,
      retryAfter: Math.round(req.rateLimit.resetTime / 1000)
    });
  }
});

/**
 * Strict rate limiting for sensitive operations
 */
const strictRateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // limit each IP to 10 requests per hour for sensitive operations
  message: {
    error: 'Rate Limit Exceeded',
    message: 'Too many sensitive operations. Please wait before retrying.',
  },
  standardHeaders: true,
  legacyHeaders: false
});

/**
 * Validation middleware for flow ownership
 */
const validateFlowOwnership = async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const flowRegistry = req.flowRegistry;

    if (!flowRegistry) {
      return res.status(503).json({
        error: 'Service Unavailable',
        message: 'Flow Registry service not available',
        requestId: req.requestId
      });
    }

    // Get flow details
    const flow = await flowRegistry.getFlow(flowId);
    if (!flow) {
      return res.status(404).json({
        error: 'Not Found',
        message: `Flow with ID '${flowId}' not found`,
        requestId: req.requestId
      });
    }

    // Service tokens can access any flow
    if (req.user.type === 'service') {
      req.flow = flow;
      return next();
    }

    // Check if user owns the flow or has admin permissions
    const isOwner = flow.createdBy === req.user.id || flow.createdBy === req.user.username;
    const isAdmin = req.user.permissions?.includes('admin') || req.user.roles?.includes('admin');

    if (!isOwner && !isAdmin) {
      logger.warn('Flow access denied', {
        requestId: req.requestId,
        userId: req.user.id,
        flowId,
        flowOwner: flow.createdBy
      });

      return res.status(403).json({
        error: 'Access Denied',
        message: 'You do not have permission to access this flow',
        requestId: req.requestId
      });
    }

    req.flow = flow;
    next();
  } catch (error) {
    logger.error('Flow ownership validation failed', {
      requestId: req.requestId,
      error: error.message,
      flowId: req.params.flowId
    });

    return res.status(500).json({
      error: 'Internal Server Error',
      message: 'Failed to validate flow ownership',
      requestId: req.requestId
    });
  }
};

/**
 * Input sanitization middleware
 */
const sanitizeInput = (req, res, next) => {
  // Remove potentially dangerous characters from string inputs
  const sanitizeString = (str) => {
    if (typeof str !== 'string') return str;
    return str.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
              .replace(/javascript:/gi, '')
              .replace(/on\w+\s*=/gi, '');
  };

  // Recursively sanitize object
  const sanitizeObject = (obj) => {
    if (obj === null || typeof obj !== 'object') {
      return typeof obj === 'string' ? sanitizeString(obj) : obj;
    }

    if (Array.isArray(obj)) {
      return obj.map(sanitizeObject);
    }

    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
      sanitized[key] = sanitizeObject(value);
    }
    return sanitized;
  };

  // Sanitize request body
  if (req.body) {
    req.body = sanitizeObject(req.body);
  }

  // Sanitize query parameters
  if (req.query) {
    req.query = sanitizeObject(req.query);
  }

  next();
};

/**
 * Flow execution audit middleware
 */
const auditFlowExecution = (req, res, next) => {
  // Capture execution context for auditing
  if (req.method === 'POST' && req.path.includes('/execute')) {
    req.auditContext = {
      action: 'flow_execution',
      flowId: req.params.flowId,
      triggeredBy: req.user?.id || 'anonymous',
      timestamp: new Date(),
      ip: req.ip,
      userAgent: req.headers['user-agent'],
      parameters: req.body?.parameters || {}
    };

    logger.info('Flow execution audit', {
      requestId: req.requestId,
      ...req.auditContext
    });
  }

  next();
};

/**
 * Error handling middleware for flow operations
 */
const flowErrorHandler = (error, req, res, next) => {
  logger.error('Flow operation error', {
    requestId: req.requestId,
    error: error.message,
    stack: error.stack,
    path: req.path,
    method: req.method,
    userId: req.user?.id,
    flowId: req.params?.flowId
  });

  // Flow validation errors
  if (error.message.includes('validation failed')) {
    return res.status(400).json({
      error: 'Flow Validation Error',
      message: error.message,
      requestId: req.requestId,
      details: error.details || null
    });
  }

  // Flow not found errors
  if (error.message.includes('not found')) {
    return res.status(404).json({
      error: 'Flow Not Found',
      message: error.message,
      requestId: req.requestId
    });
  }

  // Flow conflict errors
  if (error.message.includes('already exists')) {
    return res.status(409).json({
      error: 'Flow Conflict',
      message: error.message,
      requestId: req.requestId
    });
  }

  // Database connection errors
  if (error.code && error.code.startsWith('28')) { // PostgreSQL connection errors
    return res.status(503).json({
      error: 'Database Unavailable',
      message: 'Flow Registry database is temporarily unavailable',
      requestId: req.requestId
    });
  }

  // Default error response
  res.status(500).json({
    error: 'Internal Server Error',
    message: 'An unexpected error occurred in Flow Registry',
    requestId: req.requestId
  });
};

/**
 * CORS middleware specifically for Flow Registry
 */
const flowCors = (req, res, next) => {
  const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'];
  const origin = req.headers.origin;

  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }

  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-request-id');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  next();
};

module.exports = {
  requestId,
  requestLogger,
  authenticate,
  authorize,
  rateLimiter,
  strictRateLimiter,
  validateFlowOwnership,
  sanitizeInput,
  auditFlowExecution,
  flowErrorHandler,
  flowCors
};