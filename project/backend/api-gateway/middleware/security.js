/**
 * Security Middleware
 * Rate limiting, CORS, and other security measures
 */

const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const cors = require('cors');
const jwtConfig = require('../config/jwt');

/**
 * Rate limiting configuration
 */
const authRateLimit = rateLimit({
  windowMs: jwtConfig.rateLimitWindow,
  max: jwtConfig.rateLimitMax,
  message: {
    success: false,
    message: 'Too many requests, please try again later',
    code: 'RATE_LIMIT_EXCEEDED'
  },
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => {
    // Skip rate limiting for health checks
    return req.path === '/health' || req.path === '/api/health';
  }
});

/**
 * Strict rate limiting for authentication endpoints
 */
const strictAuthRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: {
    success: false,
    message: 'Too many authentication attempts, please try again later',
    code: 'AUTH_RATE_LIMIT_EXCEEDED'
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => {
    // Rate limit by IP and email if provided
    const email = req.body?.email || '';
    return `${req.ip}-${email}`;
  }
});

/**
 * CORS configuration
 */
const corsOptions = {
  origin: function (origin, callback) {
    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin) return callback(null, true);

    if (jwtConfig.allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS policy violation: Origin not allowed'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: [
    'Origin',
    'X-Requested-With',
    'Content-Type',
    'Accept',
    'Authorization',
    'Cache-Control',
    'X-API-Key'
  ],
  exposedHeaders: ['X-RateLimit-Limit', 'X-RateLimit-Remaining'],
  maxAge: 86400 // 24 hours
};

/**
 * Helmet security configuration
 */
const helmetOptions = {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"]
    }
  },
  crossOriginEmbedderPolicy: false,
  crossOriginResourcePolicy: { policy: "cross-origin" }
};

/**
 * Request sanitization middleware
 */
const sanitizeInput = (req, res, next) => {
  // Remove potential XSS characters
  const sanitize = (obj) => {
    if (typeof obj === 'string') {
      return obj
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/<[^>]*>?/gm, '')
        .trim();
    }

    if (Array.isArray(obj)) {
      return obj.map(sanitize);
    }

    if (obj && typeof obj === 'object') {
      const sanitized = {};
      for (const key in obj) {
        sanitized[key] = sanitize(obj[key]);
      }
      return sanitized;
    }

    return obj;
  };

  if (req.body) {
    req.body = sanitize(req.body);
  }

  if (req.query) {
    req.query = sanitize(req.query);
  }

  if (req.params) {
    req.params = sanitize(req.params);
  }

  next();
};

/**
 * Request validation middleware
 */
const validateRequest = (req, res, next) => {
  // Check for required headers
  if (!req.headers['content-type'] && (req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH')) {
    return res.status(400).json({
      success: false,
      message: 'Content-Type header is required',
      code: 'MISSING_CONTENT_TYPE'
    });
  }

  // Validate JSON content type for data requests
  if ((req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH') &&
      req.headers['content-type'] &&
      !req.headers['content-type'].includes('application/json')) {
    return res.status(400).json({
      success: false,
      message: 'Content-Type must be application/json',
      code: 'INVALID_CONTENT_TYPE'
    });
  }

  // Check request size (should be handled by express.json() limit)
  const contentLength = parseInt(req.headers['content-length'] || '0');
  if (contentLength > 1048576) { // 1MB limit
    return res.status(413).json({
      success: false,
      message: 'Request entity too large',
      code: 'REQUEST_TOO_LARGE'
    });
  }

  next();
};

/**
 * Error handling for security middleware
 */
const handleSecurityError = (err, req, res, next) => {
  if (err.message.includes('CORS policy violation')) {
    return res.status(403).json({
      success: false,
      message: 'CORS policy violation',
      code: 'CORS_VIOLATION'
    });
  }

  if (err.type === 'entity.too.large') {
    return res.status(413).json({
      success: false,
      message: 'Request entity too large',
      code: 'REQUEST_TOO_LARGE'
    });
  }

  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({
      success: false,
      message: 'Invalid JSON in request body',
      code: 'INVALID_JSON'
    });
  }

  next(err);
};

module.exports = {
  authRateLimit,
  strictAuthRateLimit,
  corsOptions,
  helmetOptions,
  sanitizeInput,
  validateRequest,
  handleSecurityError,
  helmet: helmet(helmetOptions),
  cors: cors(corsOptions)
};