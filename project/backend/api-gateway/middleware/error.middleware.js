const logger = require('../utils/logger');

class AppError extends Error {
  constructor(message, statusCode, code = null) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  logger.error(`Error ${err.statusCode || 500}: ${err.message}`, {
    error: err,
    request: {
      method: req.method,
      url: req.url,
      headers: req.headers,
      body: req.body,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    },
    user: req.auth?.user?.id || 'anonymous'
  });

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new AppError(message, 404, 'RESOURCE_NOT_FOUND');
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new AppError(message, 400, 'DUPLICATE_FIELD');
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new AppError(message, 400, 'VALIDATION_ERROR');
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token. Please log in again.';
    error = new AppError(message, 401, 'INVALID_TOKEN');
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Your token has expired. Please log in again.';
    error = new AppError(message, 401, 'TOKEN_EXPIRED');
  }

  // Rate limiting error
  if (err.statusCode === 429) {
    const message = 'Too many requests. Please try again later.';
    error = new AppError(message, 429, 'RATE_LIMIT_EXCEEDED');
  }

  // Proxy/Service errors
  if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
    const message = 'Service temporarily unavailable';
    error = new AppError(message, 503, 'SERVICE_UNAVAILABLE');
  }

  // Timeout errors
  if (err.code === 'ETIMEDOUT' || err.message?.includes('timeout')) {
    const message = 'Request timeout. Please try again.';
    error = new AppError(message, 408, 'REQUEST_TIMEOUT');
  }

  // Syntax errors
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    const message = 'Invalid JSON payload';
    error = new AppError(message, 400, 'INVALID_JSON');
  }

  // Default to 500 server error
  if (!error.statusCode) {
    error = new AppError('Internal server error', 500, 'INTERNAL_ERROR');
  }

  // Don't leak error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';

  const errorResponse = {
    error: error.message,
    code: error.code || 'UNKNOWN_ERROR',
    statusCode: error.statusCode,
    timestamp: new Date().toISOString(),
    requestId: req.id || req.headers['x-request-id'],
    path: req.originalUrl,
    method: req.method
  };

  // Add stack trace in development
  if (isDevelopment) {
    errorResponse.stack = error.stack;
    errorResponse.details = error;
  }

  // Add additional context for certain errors
  if (error.statusCode === 400) {
    errorResponse.message = 'Bad request. Please check your input.';
  } else if (error.statusCode === 401) {
    errorResponse.message = 'Authentication required or invalid.';
  } else if (error.statusCode === 403) {
    errorResponse.message = 'Insufficient permissions to access this resource.';
  } else if (error.statusCode === 404) {
    errorResponse.message = 'The requested resource was not found.';
  } else if (error.statusCode === 429) {
    errorResponse.message = 'Rate limit exceeded. Please wait before making more requests.';
  } else if (error.statusCode >= 500) {
    errorResponse.message = 'An internal server error occurred. Please try again later.';
  }

  // Send error response
  res.status(error.statusCode).json(errorResponse);
};

// Catch async errors
const catchAsync = (fn) => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (err, promise) => {
  logger.error('Unhandled Promise Rejection:', err);
  // Close server & exit process gracefully
  process.exit(1);
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception:', err);
  process.exit(1);
});

module.exports = {
  errorHandler,
  AppError,
  catchAsync
};