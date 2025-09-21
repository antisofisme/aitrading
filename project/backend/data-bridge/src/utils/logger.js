const winston = require('winston');
const path = require('path');
const config = require('../../config/config');

// Custom log format
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// Create logs directory if it doesn't exist
const fs = require('fs');
const logDir = path.dirname(config.logging.file);
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const logger = winston.createLogger({
  level: config.logging.level,
  format: logFormat,
  defaultMeta: {
    service: 'data-bridge',
    environment: config.server.environment
  },
  transports: [
    // File transport
    new winston.transports.File({
      filename: config.logging.file,
      maxsize: config.logging.maxSize,
      maxFiles: config.logging.maxFiles,
      tailable: true
    }),

    // Error file transport
    new winston.transports.File({
      filename: path.join(logDir, 'error.log'),
      level: 'error',
      maxsize: config.logging.maxSize,
      maxFiles: config.logging.maxFiles,
      tailable: true
    })
  ],
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'exceptions.log')
    })
  ],
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'rejections.log')
    })
  ]
});

// Add console transport in development
if (config.server.environment !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// Custom logging methods for trading-specific events
logger.mt5 = {
  connection: (status, details = {}) => {
    logger.info('MT5 Connection Event', {
      event: 'mt5_connection',
      status,
      ...details
    });
  },

  trade: (action, symbol, details = {}) => {
    logger.info('MT5 Trade Event', {
      event: 'mt5_trade',
      action,
      symbol,
      ...details
    });
  },

  data: (symbol, dataType, details = {}) => {
    logger.debug('MT5 Data Event', {
      event: 'mt5_data',
      symbol,
      dataType,
      ...details
    });
  },

  error: (error, context = {}) => {
    logger.error('MT5 Error', {
      event: 'mt5_error',
      error: error.message,
      stack: error.stack,
      ...context
    });
  }
};

logger.websocket = {
  connection: (clientId, action, details = {}) => {
    logger.info('WebSocket Event', {
      event: 'websocket_connection',
      clientId,
      action,
      ...details
    });
  },

  subscription: (clientId, symbol, dataType, action) => {
    logger.debug('WebSocket Subscription', {
      event: 'websocket_subscription',
      clientId,
      symbol,
      dataType,
      action
    });
  },

  error: (clientId, error, context = {}) => {
    logger.error('WebSocket Error', {
      event: 'websocket_error',
      clientId,
      error: error.message,
      ...context
    });
  }
};

logger.performance = {
  latency: (operation, duration, details = {}) => {
    logger.debug('Performance Metric', {
      event: 'performance',
      operation,
      duration,
      ...details
    });
  },

  throughput: (operation, count, timeWindow, details = {}) => {
    logger.debug('Throughput Metric', {
      event: 'throughput',
      operation,
      count,
      timeWindow,
      ...details
    });
  }
};

module.exports = logger;