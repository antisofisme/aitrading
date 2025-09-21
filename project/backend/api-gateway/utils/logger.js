const winston = require('winston');
const config = require('../config/config');

/**
 * Centralized logging utility for API Gateway
 */
class Logger {
  constructor() {
    this.logger = this.createLogger();
  }

  createLogger() {
    const logFormat = winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
      }),
      winston.format.errors({ stack: true }),
      winston.format.json(),
      winston.format.printf(({ timestamp, level, message, ...meta }) => {
        return JSON.stringify({
          timestamp,
          level,
          service: 'api-gateway',
          message,
          ...meta
        });
      })
    );

    const transports = [
      new winston.transports.Console({
        format: config.environment === 'development'
          ? winston.format.combine(
              winston.format.colorize(),
              winston.format.simple()
            )
          : logFormat
      })
    ];

    // Add file transport in production
    if (config.environment === 'production') {
      transports.push(
        new winston.transports.File({
          filename: 'logs/error.log',
          level: 'error'
        }),
        new winston.transports.File({
          filename: 'logs/combined.log'
        })
      );
    }

    return winston.createLogger({
      level: config.logging.level,
      format: logFormat,
      transports,
      exceptionHandlers: [
        new winston.transports.Console()
      ],
      rejectionHandlers: [
        new winston.transports.Console()
      ]
    });
  }

  info(message, meta = {}) {
    this.logger.info(message, meta);
  }

  error(message, meta = {}) {
    this.logger.error(message, meta);
  }

  warn(message, meta = {}) {
    this.logger.warn(message, meta);
  }

  debug(message, meta = {}) {
    this.logger.debug(message, meta);
  }

  http(message, meta = {}) {
    this.logger.http(message, meta);
  }
}

module.exports = new Logger();