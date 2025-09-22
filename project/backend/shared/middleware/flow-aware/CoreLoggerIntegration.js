/**
 * @fileoverview Core Logger Integration for flow-aware middleware
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Integrates flow-aware middleware with existing CoreLogger infrastructure
 * for consistent logging across all microservices with flow context enrichment.
 */

const path = require('path');
const winston = require('winston');

// =============================================================================
// CORE LOGGER INTEGRATION CLASS
// =============================================================================

class CoreLoggerIntegration {
  constructor(options = {}) {
    this.serviceName = options.serviceName || process.env.SERVICE_NAME || 'unknown-service';
    this.logLevel = options.logLevel || process.env.LOG_LEVEL || 'info';
    this.enableFlowContext = options.enableFlowContext !== false;
    this.enablePerformanceLogging = options.enablePerformanceLogging !== false;
    this.enableErrorCorrelation = options.enableErrorCorrelation !== false;

    // Flow-aware middleware components
    this.flowTracker = options.flowTracker;
    this.chainContextManager = options.chainContextManager;
    this.metricsCollector = options.metricsCollector;
    this.eventPublisher = options.eventPublisher;

    // Logger instance
    this.logger = null;

    this.initialize();
  }

  /**
   * Initialize enhanced logger
   */
  initialize() {
    // Create enhanced log format with flow context
    const logFormat = winston.format.combine(
      winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss.SSS'
      }),
      winston.format.errors({ stack: true }),
      winston.format.printf(this.createLogFormatter())
    );

    const transports = [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          logFormat
        )
      })
    ];

    // Add file transports in production
    if (process.env.NODE_ENV === 'production') {
      transports.push(
        new winston.transports.File({
          filename: `logs/${this.serviceName}-error.log`,
          level: 'error',
          format: winston.format.combine(
            winston.format.uncolorize(),
            winston.format.json()
          )
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}-combined.log`,
          format: winston.format.combine(
            winston.format.uncolorize(),
            winston.format.json()
          )
        })
      );
    }

    this.logger = winston.createLogger({
      level: this.logLevel,
      format: logFormat,
      transports,
      defaultMeta: {
        service: this.serviceName,
        version: process.env.SERVICE_VERSION || '1.0.0',
        environment: process.env.NODE_ENV || 'development'
      },
      exceptionHandlers: [
        new winston.transports.Console(),
        ...(process.env.NODE_ENV === 'production' ? [
          new winston.transports.File({ filename: `logs/${this.serviceName}-exceptions.log` })
        ] : [])
      ],
      rejectionHandlers: [
        new winston.transports.Console(),
        ...(process.env.NODE_ENV === 'production' ? [
          new winston.transports.File({ filename: `logs/${this.serviceName}-rejections.log` })
        ] : [])
      ]
    });
  }

  /**
   * Create log formatter with flow context
   */
  createLogFormatter() {
    return (info) => {
      const { timestamp, level, message, ...meta } = info;

      // Extract flow context if available
      const flowContext = this.extractFlowContext(meta);

      // Base log entry
      const logEntry = {
        timestamp,
        level: level.toUpperCase(),
        service: this.serviceName,
        message,
        ...meta
      };

      // Add flow context if available
      if (flowContext) {
        logEntry.flowContext = flowContext;
      }

      // Add performance metrics if enabled
      if (this.enablePerformanceLogging && meta.performance) {
        logEntry.performance = meta.performance;
      }

      // Format for console output
      if (process.env.NODE_ENV === 'development') {
        let output = `${timestamp} [${level.toUpperCase()}] ${this.serviceName}`;

        if (flowContext?.flowId) {
          output += ` [${flowContext.flowId.substring(0, 8)}]`;
        }

        output += `: ${message}`;

        if (Object.keys(meta).length > 0) {
          output += ` ${JSON.stringify(meta, null, 2)}`;
        }

        return output;
      }

      // JSON format for production
      return JSON.stringify(logEntry);
    };
  }

  /**
   * Extract flow context from metadata or current request
   */
  extractFlowContext(meta) {
    // Check if flow context is provided in meta
    if (meta.flowContext) {
      return meta.flowContext;
    }

    // Try to extract from request if available
    if (meta.req) {
      const req = meta.req;
      const flowContext = {};

      // Extract from flow tracker
      if (this.flowTracker) {
        const flow = this.flowTracker.getFlowContext(req);
        if (flow) {
          flowContext.flowId = flow.flowId;
          flowContext.correlationId = flow.correlationId;
          flowContext.parentFlowId = flow.parentFlowId;
          flowContext.serviceChain = flow.serviceChain;
        }
      }

      // Extract from chain context manager
      if (this.chainContextManager) {
        const chain = this.chainContextManager.getContext(req);
        if (chain) {
          flowContext.contextId = chain.id;
          flowContext.rootContextId = chain.rootId;
          flowContext.depth = chain.depth;
        }
      }

      return Object.keys(flowContext).length > 0 ? flowContext : null;
    }

    return null;
  }

  /**
   * Enhanced info logging with flow context
   */
  info(message, meta = {}) {
    this.logger.info(message, this.enrichMeta(meta));
  }

  /**
   * Enhanced error logging with flow context and correlation
   */
  error(message, meta = {}) {
    const enrichedMeta = this.enrichMeta(meta);

    // Add error correlation if enabled
    if (this.enableErrorCorrelation && enrichedMeta.error) {
      enrichedMeta.errorCorrelation = this.createErrorCorrelation(enrichedMeta);
    }

    this.logger.error(message, enrichedMeta);

    // Publish error event if event publisher available
    if (this.eventPublisher && enrichedMeta.flowContext) {
      this.eventPublisher.publish('error.logged', {
        serviceName: this.serviceName,
        message,
        flowId: enrichedMeta.flowContext.flowId,
        correlationId: enrichedMeta.flowContext.correlationId,
        error: enrichedMeta.error,
        timestamp: Date.now()
      }, {
        priority: 3 // High priority
      });
    }
  }

  /**
   * Enhanced warn logging with flow context
   */
  warn(message, meta = {}) {
    this.logger.warn(message, this.enrichMeta(meta));
  }

  /**
   * Enhanced debug logging with flow context
   */
  debug(message, meta = {}) {
    this.logger.debug(message, this.enrichMeta(meta));
  }

  /**
   * HTTP request logging
   */
  http(message, meta = {}) {
    const enrichedMeta = this.enrichMeta(meta);

    // Add performance metrics if available
    if (this.enablePerformanceLogging && meta.req) {
      const req = meta.req;

      // Get flow metrics
      if (this.flowTracker) {
        const flowMetrics = this.flowTracker.getFlowMetrics(req);
        if (flowMetrics) {
          enrichedMeta.performance = flowMetrics;
        }
      }

      // Get chain metrics
      if (this.chainContextManager) {
        const chainMetrics = this.chainContextManager.getMetrics(req);
        if (chainMetrics) {
          enrichedMeta.chainMetrics = chainMetrics;
        }
      }
    }

    this.logger.http(message, enrichedMeta);
  }

  /**
   * Enrich metadata with flow context
   */
  enrichMeta(meta) {
    const enriched = { ...meta };

    // Add timestamp if not present
    if (!enriched.timestamp) {
      enriched.timestamp = Date.now();
    }

    // Add flow context if enabled and not already present
    if (this.enableFlowContext && !enriched.flowContext) {
      const flowContext = this.extractFlowContext(enriched);
      if (flowContext) {
        enriched.flowContext = flowContext;
      }
    }

    // Add service metadata
    enriched.serviceMetadata = {
      serviceName: this.serviceName,
      version: process.env.SERVICE_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      nodeVersion: process.version,
      pid: process.pid
    };

    return enriched;
  }

  /**
   * Create error correlation data
   */
  createErrorCorrelation(meta) {
    const correlation = {
      timestamp: Date.now(),
      serviceName: this.serviceName
    };

    // Add flow context
    if (meta.flowContext) {
      correlation.flowId = meta.flowContext.flowId;
      correlation.correlationId = meta.flowContext.correlationId;
      correlation.serviceChain = meta.flowContext.serviceChain;
    }

    // Add error details
    if (meta.error) {
      correlation.errorType = meta.error.constructor.name;
      correlation.errorCode = meta.error.code;
      correlation.errorMessage = meta.error.message;
    }

    // Add request context
    if (meta.req) {
      correlation.requestPath = meta.req.path;
      correlation.requestMethod = meta.req.method;
      correlation.userAgent = meta.req.get('user-agent');
      correlation.clientIp = meta.req.ip;
    }

    return correlation;
  }

  /**
   * Create flow-aware middleware for Express.js
   */
  createMiddleware() {
    return (req, res, next) => {
      // Add logger to request for easy access
      req.logger = this.createRequestLogger(req);

      // Override res.end to log response
      const originalEnd = res.end;
      res.end = (...args) => {
        const duration = Date.now() - req.startTime;

        req.logger.http('Request completed', {
          method: req.method,
          path: req.path,
          statusCode: res.statusCode,
          duration,
          userAgent: req.get('user-agent'),
          clientIp: req.ip
        });

        return originalEnd.apply(res, args);
      };

      // Set request start time
      req.startTime = Date.now();

      next();
    };
  }

  /**
   * Create request-specific logger
   */
  createRequestLogger(req) {
    return {
      info: (message, meta = {}) => this.info(message, { ...meta, req }),
      error: (message, meta = {}) => this.error(message, { ...meta, req }),
      warn: (message, meta = {}) => this.warn(message, { ...meta, req }),
      debug: (message, meta = {}) => this.debug(message, { ...meta, req }),
      http: (message, meta = {}) => this.http(message, { ...meta, req })
    };
  }

  /**
   * Log flow events
   */
  logFlowEvent(eventType, data, req = null) {
    const meta = { eventType, data };
    if (req) meta.req = req;

    switch (eventType) {
      case 'flow.start':
        this.info('Flow started', meta);
        break;
      case 'flow.complete':
        this.info('Flow completed', meta);
        break;
      case 'flow.error':
        this.error('Flow error occurred', meta);
        break;
      case 'dependency.call':
        this.debug('Dependency called', meta);
        break;
      default:
        this.debug('Flow event', meta);
    }
  }

  /**
   * Get logger instance
   */
  getLogger() {
    return this.logger;
  }

  /**
   * Get enhanced logger with flow context support
   */
  getEnhancedLogger() {
    return {
      info: this.info.bind(this),
      error: this.error.bind(this),
      warn: this.warn.bind(this),
      debug: this.debug.bind(this),
      http: this.http.bind(this),
      logFlowEvent: this.logFlowEvent.bind(this),
      createRequestLogger: this.createRequestLogger.bind(this),
      getLogger: this.getLogger.bind(this)
    };
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create CoreLoggerIntegration instance
 */
function createCoreLoggerIntegration(options = {}) {
  return new CoreLoggerIntegration(options);
}

/**
 * Setup enhanced logging for existing logger
 */
function enhanceExistingLogger(existingLogger, flowAwareComponents = {}) {
  const integration = new CoreLoggerIntegration({
    ...flowAwareComponents,
    existingLogger
  });

  return integration.getEnhancedLogger();
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  CoreLoggerIntegration,
  createCoreLoggerIntegration,
  enhanceExistingLogger
};