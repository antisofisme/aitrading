/**
 * Logger Utility
 * Centralized logging configuration
 */

import winston from 'winston';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create logs directory if it doesn't exist
import fs from 'fs';
const logsDir = path.resolve(__dirname, '../../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Configure log levels and colors
const logLevels = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3
};

const logColors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  debug: 'blue'
};

winston.addColors(logColors);

// Create logger configuration
const loggerConfig = {
  level: process.env.LOG_LEVEL || 'info',
  levels: logLevels,
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss.SSS'
    }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'chain-debug-system',
    version: process.env.npm_package_version || '1.0.0'
  },
  transports: []
};

// Console transport
if (process.env.NODE_ENV !== 'production') {
  loggerConfig.transports.push(
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple(),
        winston.format.printf(({ timestamp, level, message, service, ...meta }) => {
          const metaStr = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
          return `${timestamp} [${service}] ${level}: ${message} ${metaStr}`;
        })
      )
    })
  );
}

// File transport
loggerConfig.transports.push(
  new winston.transports.File({
    filename: path.join(logsDir, 'error.log'),
    level: 'error',
    maxsize: 5242880, // 5MB
    maxFiles: 5,
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    )
  })
);

loggerConfig.transports.push(
  new winston.transports.File({
    filename: path.join(logsDir, 'combined.log'),
    maxsize: 5242880, // 5MB
    maxFiles: 5,
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    )
  })
);

// Create logger instance
const logger = winston.createLogger(loggerConfig);

// Enhanced logging methods
logger.chain = (chainId) => {
  return {
    info: (message, meta = {}) => logger.info(message, { chainId, ...meta }),
    warn: (message, meta = {}) => logger.warn(message, { chainId, ...meta }),
    error: (message, meta = {}) => logger.error(message, { chainId, ...meta }),
    debug: (message, meta = {}) => logger.debug(message, { chainId, ...meta })
  };
};

logger.component = (componentName) => {
  return {
    info: (message, meta = {}) => logger.info(message, { component: componentName, ...meta }),
    warn: (message, meta = {}) => logger.warn(message, { component: componentName, ...meta }),
    error: (message, meta = {}) => logger.error(message, { component: componentName, ...meta }),
    debug: (message, meta = {}) => logger.debug(message, { component: componentName, ...meta })
  };
};

logger.anomaly = (anomaly) => {
  return {
    detected: (message, meta = {}) => logger.warn(message, {
      anomalyType: anomaly.type,
      severity: anomaly.severity,
      chainId: anomaly.chainId,
      confidence: anomaly.confidence,
      ...meta
    }),
    resolved: (message, meta = {}) => logger.info(message, {
      anomalyType: anomaly.type,
      severity: anomaly.severity,
      chainId: anomaly.chainId,
      ...meta
    })
  };
};

logger.performance = (operation, startTime, meta = {}) => {
  const duration = Date.now() - startTime;
  logger.info(`Performance: ${operation} completed`, {
    operation,
    duration,
    ...meta
  });
  return duration;
};

logger.recovery = (chainId) => {
  return {
    started: (message, meta = {}) => logger.info(message, {
      chainId,
      recoveryPhase: 'started',
      ...meta
    }),
    progress: (message, meta = {}) => logger.info(message, {
      chainId,
      recoveryPhase: 'progress',
      ...meta
    }),
    completed: (message, meta = {}) => logger.info(message, {
      chainId,
      recoveryPhase: 'completed',
      ...meta
    }),
    failed: (message, meta = {}) => logger.error(message, {
      chainId,
      recoveryPhase: 'failed',
      ...meta
    })
  };
};

// Error handling for logger itself
logger.on('error', (error) => {
  console.error('Logger error:', error);
});

// Graceful shutdown
process.on('SIGINT', () => {
  logger.info('Received SIGINT, closing logger...');
  logger.end();
});

process.on('SIGTERM', () => {
  logger.info('Received SIGTERM, closing logger...');
  logger.end();
});

export default logger;