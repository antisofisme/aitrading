const logger = require('../utils/logger');

/**
 * Global error handler middleware for API Gateway
 */
function errorHandler(err, req, res, next) {
  logger.error('Unhandled error:', {
    error: err.message,
    stack: err.stack,
    method: req.method,
    path: req.path,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // Default error
  let status = 500;
  let message = 'Internal server error';
  let details = null;

  // Handle specific error types
  if (err.name === 'ValidationError') {
    status = 400;
    message = 'Validation error';
    details = err.details;
  } else if (err.name === 'UnauthorizedError' || err.status === 401) {
    status = 401;
    message = 'Unauthorized';
  } else if (err.status === 403) {
    status = 403;
    message = 'Forbidden';
  } else if (err.status === 404) {
    status = 404;
    message = 'Not found';
  } else if (err.name === 'SyntaxError' && err.status === 400) {
    status = 400;
    message = 'Invalid JSON';
  } else if (err.code === 'ECONNREFUSED' || err.code === 'ETIMEDOUT') {
    status = 502;
    message = 'Service unavailable';
    details = 'Downstream service is not responding';
  }

  // Build error response
  const errorResponse = {
    error: message,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  };

  // Add details in development mode
  if (process.env.NODE_ENV === 'development') {
    errorResponse.details = details || err.message;
    errorResponse.stack = err.stack;
  }

  res.status(status).json(errorResponse);
}

module.exports = errorHandler;