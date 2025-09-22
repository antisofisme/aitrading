const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const logger = require('../config/logger');

/**
 * PCI DSS Compliance Security Middleware
 */

/**
 * Rate limiting middleware
 */
const createRateLimit = (windowMs, max, message) => {
  return rateLimit({
    windowMs,
    max,
    message: {
      success: false,
      message: message || 'Too many requests, please try again later'
    },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      logger.warn('🚫 Rate limit exceeded', {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        endpoint: req.path
      });

      res.status(429).json({
        success: false,
        message: 'Too many requests, please try again later'
      });
    }
  });
};

/**
 * General API rate limiting
 */
const apiRateLimit = createRateLimit(
  15 * 60 * 1000, // 15 minutes
  100, // max 100 requests per 15 minutes
  'Too many API requests, please try again later'
);

/**
 * Payment creation rate limiting
 */
const paymentRateLimit = createRateLimit(
  5 * 60 * 1000, // 5 minutes
  10, // max 10 payment attempts per 5 minutes
  'Too many payment attempts, please try again later'
);

/**
 * Webhook rate limiting
 */
const webhookRateLimit = createRateLimit(
  1 * 60 * 1000, // 1 minute
  50, // max 50 webhook calls per minute
  'Too many webhook requests'
);

/**
 * Security headers middleware (PCI DSS compliance)
 */
const securityHeaders = helmet({
  // Force HTTPS
  hsts: {
    maxAge: 31536000, // 1 year
    includeSubDomains: true,
    preload: true
  },

  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.midtrans.com", "https://app.midtrans.com"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"]
    }
  },

  // Prevent MIME type sniffing
  noSniff: true,

  // Prevent clickjacking
  frameguard: { action: 'deny' },

  // XSS protection
  xssFilter: true,

  // Referrer policy
  referrerPolicy: { policy: 'same-origin' },

  // Cross-origin policies
  crossOriginEmbedderPolicy: false, // Disable for API compatibility
  crossOriginOpenerPolicy: false,
  crossOriginResourcePolicy: { policy: 'cross-origin' }
});

/**
 * Request sanitization middleware
 */
const sanitizeRequest = (req, res, next) => {
  try {
    // Remove null bytes (security vulnerability)
    const removeNullBytes = (obj) => {
      if (typeof obj === 'string') {
        return obj.replace(/\0/g, '');
      }

      if (Array.isArray(obj)) {
        return obj.map(removeNullBytes);
      }

      if (obj !== null && typeof obj === 'object') {
        const cleaned = {};
        for (const [key, value] of Object.entries(obj)) {
          cleaned[key] = removeNullBytes(value);
        }
        return cleaned;
      }

      return obj;
    };

    // Sanitize request body
    if (req.body) {
      req.body = removeNullBytes(req.body);
    }

    // Sanitize query parameters
    if (req.query) {
      req.query = removeNullBytes(req.query);
    }

    // Sanitize URL parameters
    if (req.params) {
      req.params = removeNullBytes(req.params);
    }

    next();

  } catch (error) {
    logger.error('❌ Request sanitization failed', {
      error: error.message,
      ip: req.ip
    });

    res.status(400).json({
      success: false,
      message: 'Invalid request format'
    });
  }
};

/**
 * IP whitelisting middleware for admin endpoints
 */
const ipWhitelist = (req, res, next) => {
  const allowedIPs = process.env.ADMIN_ALLOWED_IPS?.split(',') || [];

  if (allowedIPs.length === 0) {
    return next(); // Skip if no whitelist configured
  }

  const clientIP = req.ip || req.connection.remoteAddress;

  if (!allowedIPs.includes(clientIP)) {
    logger.warn('🚫 IP not whitelisted for admin access', {
      ip: clientIP,
      endpoint: req.path
    });

    return res.status(403).json({
      success: false,
      message: 'Access denied'
    });
  }

  next();
};

/**
 * JWT authentication middleware
 */
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    // Check for service token in headers
    const serviceToken = req.headers['x-service-token'];
    if (serviceToken && serviceToken === process.env.SERVICE_TOKEN) {
      req.user = { isService: true };
      return next();
    }

    return res.status(401).json({
      success: false,
      message: 'Authentication token required'
    });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      logger.warn('🚫 Invalid authentication token', {
        error: err.message,
        ip: req.ip
      });

      return res.status(403).json({
        success: false,
        message: 'Invalid authentication token'
      });
    }

    req.user = user;
    next();
  });
};

/**
 * Admin authorization middleware
 */
const requireAdmin = (req, res, next) => {
  if (!req.user?.isAdmin && !req.user?.isService) {
    logger.warn('🚫 Unauthorized admin access attempt', {
      userId: req.user?.id,
      ip: req.ip,
      endpoint: req.path
    });

    return res.status(403).json({
      success: false,
      message: 'Admin access required'
    });
  }

  next();
};

/**
 * Webhook signature verification middleware
 */
const verifyWebhookSignature = (req, res, next) => {
  try {
    const signature = req.headers['x-midtrans-signature'] || req.headers['signature'];

    if (!signature) {
      logger.warn('⚠️ Webhook received without signature', {
        ip: req.ip,
        orderId: req.body?.order_id
      });

      return res.status(400).json({
        success: false,
        message: 'Webhook signature required'
      });
    }

    // Signature will be verified in the service layer
    // This middleware just ensures signature header exists
    next();

  } catch (error) {
    logger.error('❌ Webhook signature verification failed', {
      error: error.message,
      ip: req.ip
    });

    res.status(400).json({
      success: false,
      message: 'Invalid webhook signature'
    });
  }
};

/**
 * Request logging middleware (PCI DSS audit requirements)
 */
const auditLogger = (req, res, next) => {
  const startTime = Date.now();

  // Log request
  logger.info('📥 Request received', {
    method: req.method,
    path: req.path,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: req.user?.id,
    timestamp: new Date().toISOString()
  });

  // Capture original send method
  const originalSend = res.send;

  res.send = function(data) {
    const duration = Date.now() - startTime;

    // Log response
    logger.info('📤 Request completed', {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
      userId: req.user?.id,
      timestamp: new Date().toISOString()
    });

    // Call original send method
    originalSend.call(this, data);
  };

  next();
};

/**
 * Input validation middleware for sensitive fields
 */
const validateSensitiveInput = (req, res, next) => {
  try {
    // Check for potential SQL injection patterns
    const sqlInjectionPattern = /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)|(\-\-)|(\;)|(\bOR\b.*=.*)|(\bAND\b.*=.*)/i;

    // Check for XSS patterns
    const xssPattern = /<script|javascript:|data:text\/html|vbscript:|onclick|onerror|onload/i;

    const checkString = (str, fieldName) => {
      if (typeof str !== 'string') return;

      if (sqlInjectionPattern.test(str)) {
        throw new Error(`Potential SQL injection detected in ${fieldName}`);
      }

      if (xssPattern.test(str)) {
        throw new Error(`Potential XSS detected in ${fieldName}`);
      }
    };

    const validateObject = (obj, path = '') => {
      for (const [key, value] of Object.entries(obj)) {
        const fieldPath = path ? `${path}.${key}` : key;

        if (typeof value === 'string') {
          checkString(value, fieldPath);
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            if (typeof item === 'string') {
              checkString(item, `${fieldPath}[${index}]`);
            } else if (typeof item === 'object' && item !== null) {
              validateObject(item, `${fieldPath}[${index}]`);
            }
          });
        } else if (typeof value === 'object' && value !== null) {
          validateObject(value, fieldPath);
        }
      }
    };

    // Validate request body
    if (req.body && typeof req.body === 'object') {
      validateObject(req.body, 'body');
    }

    // Validate query parameters
    if (req.query && typeof req.query === 'object') {
      validateObject(req.query, 'query');
    }

    next();

  } catch (error) {
    logger.warn('🚫 Security validation failed', {
      error: error.message,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      endpoint: req.path
    });

    res.status(400).json({
      success: false,
      message: 'Invalid input detected'
    });
  }
};

/**
 * CORS configuration for payment service
 */
const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [
      'http://localhost:3000',
      'http://localhost:3001',
      'https://trading.neliti.com'
    ];

    // Allow requests with no origin (mobile apps, etc.)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      logger.warn('🚫 CORS blocked request', { origin });
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Origin',
    'X-Requested-With',
    'Content-Type',
    'Accept',
    'Authorization',
    'X-User-ID',
    'X-Service-Token',
    'X-Midtrans-Signature'
  ],
  exposedHeaders: ['X-Total-Count', 'X-Rate-Limit-Remaining'],
  maxAge: 86400 // 24 hours
};

module.exports = {
  securityHeaders,
  apiRateLimit,
  paymentRateLimit,
  webhookRateLimit,
  sanitizeRequest,
  ipWhitelist,
  authenticateToken,
  requireAdmin,
  verifyWebhookSignature,
  auditLogger,
  validateSensitiveInput,
  corsOptions
};