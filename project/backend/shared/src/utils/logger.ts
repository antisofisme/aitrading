/**
 * @fileoverview Centralized logging utility for AI Trading Platform
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import { LogEntry, LogContext, LogLevel } from '../types';

// =============================================================================
// LOGGER CONFIGURATION
// =============================================================================

export interface LoggerConfig {
  service: string;
  version: string;
  environment: string;
  level: string;
  enableConsole: boolean;
  enableFile: boolean;
  enableRotation: boolean;
  filePath?: string;
  maxSize?: string;
  maxFiles?: string;
  format?: 'json' | 'simple' | 'combined';
}

const defaultConfig: LoggerConfig = {
  service: 'unknown',
  version: '1.0.0',
  environment: process.env.NODE_ENV || 'development',
  level: process.env.LOG_LEVEL || 'info',
  enableConsole: true,
  enableFile: true,
  enableRotation: true,
  filePath: './logs',
  maxSize: '20m',
  maxFiles: '14d',
  format: 'json'
};

// =============================================================================
// LOGGER CLASS
// =============================================================================

export class Logger {
  private winston: winston.Logger;
  private config: LoggerConfig;
  private context: Partial<LogContext> = {};

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
    this.winston = this.createLogger();
  }

  /**
   * Create Winston logger instance with configured transports
   */
  private createLogger(): winston.Logger {
    const transports: winston.transport[] = [];

    // Console transport
    if (this.config.enableConsole) {
      transports.push(new winston.transports.Console({
        format: this.config.environment === 'production'
          ? winston.format.json()
          : winston.format.combine(
              winston.format.colorize(),
              winston.format.timestamp(),
              winston.format.printf(({ level, message, timestamp, ...meta }) => {
                return `${timestamp} [${level}] ${message} ${Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''}`;
              })
            )
      }));
    }

    // File transport
    if (this.config.enableFile) {
      if (this.config.enableRotation) {
        // Rotating file transport
        transports.push(new DailyRotateFile({
          filename: `${this.config.filePath}/${this.config.service}-%DATE%.log`,
          datePattern: 'YYYY-MM-DD',
          maxSize: this.config.maxSize,
          maxFiles: this.config.maxFiles,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        }));

        // Error logs
        transports.push(new DailyRotateFile({
          filename: `${this.config.filePath}/${this.config.service}-error-%DATE%.log`,
          datePattern: 'YYYY-MM-DD',
          level: 'error',
          maxSize: this.config.maxSize,
          maxFiles: this.config.maxFiles,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        }));
      } else {
        // Simple file transport
        transports.push(new winston.transports.File({
          filename: `${this.config.filePath}/${this.config.service}.log`,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        }));
      }
    }

    return winston.createLogger({
      level: this.config.level,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: {
        service: this.config.service,
        version: this.config.version,
        environment: this.config.environment
      },
      transports,
      exitOnError: false
    });
  }

  /**
   * Set global context for all log entries
   */
  setContext(context: Partial<LogContext>): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * Create child logger with additional context
   */
  child(context: Partial<LogContext>): Logger {
    const childLogger = new Logger(this.config);
    childLogger.setContext({ ...this.context, ...context });
    return childLogger;
  }

  /**
   * Log error message
   */
  error(message: string, data?: Record<string, unknown>, error?: Error): void {
    this.log('error', message, data, error);
  }

  /**
   * Log warning message
   */
  warn(message: string, data?: Record<string, unknown>): void {
    this.log('warn', message, data);
  }

  /**
   * Log info message
   */
  info(message: string, data?: Record<string, unknown>): void {
    this.log('info', message, data);
  }

  /**
   * Log debug message
   */
  debug(message: string, data?: Record<string, unknown>): void {
    this.log('debug', message, data);
  }

  /**
   * Log trace message
   */
  trace(message: string, data?: Record<string, unknown>): void {
    this.log('trace', message, data);
  }

  /**
   * Log audit event
   */
  audit(event: string, data?: Record<string, unknown>): void {
    this.log('info', `AUDIT: ${event}`, { ...data, audit: true });
  }

  /**
   * Log performance metric
   */
  performance(operation: string, duration: number, data?: Record<string, unknown>): void {
    this.log('info', `PERFORMANCE: ${operation}`, {
      ...data,
      performance: true,
      duration,
      operation
    });
  }

  /**
   * Log security event
   */
  security(event: string, data?: Record<string, unknown>): void {
    this.log('warn', `SECURITY: ${event}`, { ...data, security: true });
  }

  /**
   * Internal log method
   */
  private log(
    level: LogLevel['level'],
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ): void {
    const logEntry: Partial<LogEntry> = {
      level,
      message,
      timestamp: new Date(),
      context: {
        service: this.config.service,
        version: this.config.version,
        environment: this.config.environment,
        ...this.context
      },
      data,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } as Error : undefined
    };

    this.winston.log(level, message, logEntry);
  }

  /**
   * Get underlying Winston logger
   */
  getWinstonLogger(): winston.Logger {
    return this.winston;
  }

  /**
   * Create structured log entry
   */
  createLogEntry(
    level: LogLevel['level'],
    message: string,
    data?: Record<string, unknown>
  ): LogEntry {
    return {
      level,
      message,
      timestamp: new Date(),
      context: {
        service: this.config.service,
        version: this.config.version,
        environment: this.config.environment,
        ...this.context
      },
      data
    };
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create logger instance with service configuration
 */
export function createLogger(config: Partial<LoggerConfig>): Logger {
  return new Logger(config);
}

/**
 * Create service-specific logger
 */
export function createServiceLogger(
  serviceName: string,
  version: string = '1.0.0'
): Logger {
  return new Logger({
    service: serviceName,
    version,
    environment: process.env.NODE_ENV || 'development'
  });
}

/**
 * Request logging middleware factory
 */
export function createRequestLogger(logger: Logger) {
  return (req: any, res: any, next: any) => {
    const startTime = Date.now();
    const requestId = req.headers['x-request-id'] || generateRequestId();

    // Set request context
    req.logger = logger.child({
      requestId,
      userId: req.user?.id,
      method: req.method,
      url: req.url,
      userAgent: req.get('user-agent'),
      ip: req.ip
    });

    // Log request start
    req.logger.info('Request started', {
      method: req.method,
      url: req.url,
      headers: filterSensitiveHeaders(req.headers),
      query: req.query
    });

    // Log response
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      req.logger.info('Request completed', {
        statusCode: res.statusCode,
        duration,
        contentLength: res.get('content-length')
      });
    });

    next();
  };
}

/**
 * Generate unique request ID
 */
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Filter sensitive information from headers
 */
function filterSensitiveHeaders(headers: Record<string, any>): Record<string, any> {
  const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key'];
  const filtered = { ...headers };

  sensitiveHeaders.forEach(header => {
    if (filtered[header]) {
      filtered[header] = '[REDACTED]';
    }
  });

  return filtered;
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default Logger;