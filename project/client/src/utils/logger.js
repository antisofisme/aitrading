const winston = require('winston');
const path = require('path');
const fs = require('fs');

// Ensure logs directory exists
const logsDir = path.join(__dirname, '../../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
);

// Console format for development
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'HH:mm:ss.SSS' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let log = `${timestamp} [${level}] ${message}`;

    if (Object.keys(meta).length > 0) {
      log += ` ${JSON.stringify(meta)}`;
    }

    return log;
  })
);

// Create logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: {
    service: 'ai-trading-client',
    version: '1.0.0',
    pid: process.pid
  },
  transports: [
    // File transport for all logs
    new winston.transports.File({
      filename: path.join(logsDir, 'client.log'),
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    }),

    // Separate file for errors
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    }),

    // Console transport for development
    new winston.transports.Console({
      format: consoleFormat,
      level: process.env.NODE_ENV === 'production' ? 'warn' : 'debug'
    })
  ],

  // Handle uncaught exceptions
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'exceptions.log'),
      maxsize: 10 * 1024 * 1024,
      maxFiles: 3
    })
  ],

  // Handle unhandled promise rejections
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'rejections.log'),
      maxsize: 10 * 1024 * 1024,
      maxFiles: 3
    })
  ]
});

// Add custom methods for specific use cases
logger.performance = (message, metrics) => {
  logger.info(message, { type: 'performance', metrics });
};

logger.security = (message, details) => {
  logger.warn(message, { type: 'security', details });
};

logger.trading = (message, data) => {
  logger.info(message, { type: 'trading', data });
};

logger.mt5 = (message, details) => {
  logger.info(message, { type: 'mt5', details });
};

logger.websocket = (message, details) => {
  logger.debug(message, { type: 'websocket', details });
};

module.exports = logger;