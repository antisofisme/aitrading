const Joi = require('joi');
const logger = require('../utils/logger');
const config = require('../../config/config');

// WebSocket connection validation
const validateConnection = (info) => {
  const { req } = info;
  const clientIP = req.socket.remoteAddress;

  // Check IP whitelist if configured
  if (config.security.allowedIPs.length > 0) {
    if (!config.security.allowedIPs.includes(clientIP)) {
      logger.warn(`Connection rejected from unauthorized IP: ${clientIP}`);
      return false;
    }
  }

  // Check connection limit
  // This would be implemented with a connection counter
  // For now, just log the connection attempt
  logger.info(`WebSocket connection attempt from: ${clientIP}`);

  return true;
};

// Request validation schemas
const schemas = {
  subscription: Joi.object({
    type: Joi.string().valid('subscribe').required(),
    symbol: Joi.string().required().pattern(/^[A-Z]{6}$/),
    dataType: Joi.string().valid('tick', 'quote', 'bar', 'book').required(),
    interval: Joi.string().valid('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1').optional()
  }),

  unsubscription: Joi.object({
    type: Joi.string().valid('unsubscribe').required(),
    symbol: Joi.string().required().pattern(/^[A-Z]{6}$/),
    dataType: Joi.string().valid('tick', 'quote', 'bar', 'book').required()
  }),

  marketDataRequest: Joi.object({
    symbol: Joi.string().required().pattern(/^[A-Z]{6}$/),
    from: Joi.date().iso().optional(),
    to: Joi.date().iso().optional(),
    limit: Joi.number().integer().min(1).max(10000).default(100)
  })
};

// Validation middleware
const validateRequest = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body || req.query || req.params, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const details = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      logger.warn('Request validation failed', {
        path: req.path,
        method: req.method,
        errors: details,
        ip: req.ip
      });

      return res.status(400).json({
        error: 'Validation failed',
        details
      });
    }

    // Attach validated data to request
    req.validated = value;
    next();
  };
};

// WebSocket message validation
const validateWebSocketMessage = (message) => {
  try {
    const parsed = typeof message === 'string' ? JSON.parse(message) : message;

    // Basic structure validation
    if (!parsed.type) {
      return { isValid: false, error: 'Message type is required' };
    }

    // Validate based on message type
    let schema;
    switch (parsed.type) {
      case 'subscribe':
        schema = schemas.subscription;
        break;
      case 'unsubscribe':
        schema = schemas.unsubscription;
        break;
      case 'ping':
        // Ping messages don't need additional validation
        return { isValid: true, data: parsed };
      default:
        return { isValid: false, error: `Unknown message type: ${parsed.type}` };
    }

    const { error, value } = schema.validate(parsed);
    if (error) {
      return {
        isValid: false,
        error: error.details.map(d => d.message).join(', ')
      };
    }

    return { isValid: true, data: value };

  } catch (err) {
    return { isValid: false, error: 'Invalid JSON format' };
  }
};

// Symbol validation
const isValidSymbol = (symbol) => {
  // MT5 symbols are typically 6 characters for major pairs
  // This can be extended for other instrument types
  const symbolPattern = /^[A-Z]{6}$/;
  return symbolPattern.test(symbol);
};

// Data type validation
const isValidDataType = (dataType) => {
  const validTypes = ['tick', 'quote', 'bar', 'book'];
  return validTypes.includes(dataType);
};

// Rate limiting (simple in-memory implementation)
const rateLimiter = new Map();

const checkRateLimit = (identifier, windowMs = 900000, maxRequests = 100) => {
  const now = Date.now();
  const windowStart = now - windowMs;

  if (!rateLimiter.has(identifier)) {
    rateLimiter.set(identifier, []);
  }

  const requests = rateLimiter.get(identifier);

  // Remove old requests outside the window
  const validRequests = requests.filter(timestamp => timestamp > windowStart);

  if (validRequests.length >= maxRequests) {
    return false;
  }

  validRequests.push(now);
  rateLimiter.set(identifier, validRequests);

  return true;
};

// Clean up old rate limit entries periodically
setInterval(() => {
  const now = Date.now();
  const windowMs = config.security.rateLimitWindow;

  rateLimiter.forEach((requests, identifier) => {
    const validRequests = requests.filter(timestamp => timestamp > now - windowMs);
    if (validRequests.length === 0) {
      rateLimiter.delete(identifier);
    } else {
      rateLimiter.set(identifier, validRequests);
    }
  });
}, 300000); // Clean up every 5 minutes

module.exports = {
  validateConnection,
  validateRequest,
  validateWebSocketMessage,
  isValidSymbol,
  isValidDataType,
  checkRateLimit,
  schemas
};