/**
 * Flow-Aware Error Handling Middleware
 *
 * Integrates with Configuration Service's Flow Registry to provide
 * context-aware error handling and recovery strategies.
 */

const FlowRegistryClient = require('../../configuration-service/src/client/FlowRegistryClient');
const winston = require('winston');

class FlowAwareErrorHandler {
  constructor(options = {}) {
    this.logger = options.logger || winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'logs/flow-error-handler.log' })
      ]
    });

    this.flowRegistryClient = new FlowRegistryClient({
      baseURL: process.env.FLOW_REGISTRY_URL || 'http://configuration-service:8012',
      timeout: 30000,
      retryAttempts: 3
    });

    this.errorPatterns = new Map();
    this.recoveryStrategies = new Map();
    this.flowContext = new Map();

    this.initializeErrorPatterns();
    this.initializeRecoveryStrategies();
  }

  /**
   * Initialize common error patterns and their flow mappings
   */
  initializeErrorPatterns() {
    // Database connection errors
    this.errorPatterns.set('DATABASE_CONNECTION_ERROR', {
      patterns: [
        /connection terminated/i,
        /connect ECONNREFUSED/i,
        /timeout/i,
        /connection pool exhausted/i
      ],
      flowType: 'database_error_recovery',
      severity: 'high',
      category: 'infrastructure'
    });

    // Authentication errors
    this.errorPatterns.set('AUTHENTICATION_ERROR', {
      patterns: [
        /unauthorized/i,
        /invalid token/i,
        /token expired/i,
        /authentication failed/i
      ],
      flowType: 'auth_error_recovery',
      severity: 'medium',
      category: 'security'
    });

    // Rate limiting errors
    this.errorPatterns.set('RATE_LIMIT_ERROR', {
      patterns: [
        /rate limit exceeded/i,
        /too many requests/i,
        /quota exceeded/i
      ],
      flowType: 'rate_limit_recovery',
      severity: 'low',
      category: 'throttling'
    });

    // Service discovery errors
    this.errorPatterns.set('SERVICE_DISCOVERY_ERROR', {
      patterns: [
        /service not found/i,
        /service unavailable/i,
        /circuit breaker/i,
        /upstream connect error/i
      ],
      flowType: 'service_discovery_recovery',
      severity: 'high',
      category: 'service_mesh'
    });

    // Validation errors
    this.errorPatterns.set('VALIDATION_ERROR', {
      patterns: [
        /validation failed/i,
        /invalid input/i,
        /schema validation error/i,
        /bad request/i
      ],
      flowType: 'validation_error_recovery',
      severity: 'low',
      category: 'validation'
    });
  }

  /**
   * Initialize recovery strategies
   */
  initializeRecoveryStrategies() {
    // Database recovery strategy
    this.recoveryStrategies.set('database_error_recovery', {
      immediate: async (error, context) => {
        // Try alternative database connection
        if (context.databaseManager) {
          const healthStatus = await context.databaseManager.healthCheck();
          const healthyDbs = Object.entries(healthStatus)
            .filter(([db, status]) => status.status === 'healthy')
            .map(([db]) => db);

          if (healthyDbs.length > 0) {
            return {
              action: 'retry_with_fallback',
              fallbackDatabase: healthyDbs[0],
              retryAfter: 1000
            };
          }
        }
        return { action: 'circuit_breaker', retryAfter: 5000 };
      },
      delayed: async (error, context) => {
        // Attempt database reconnection
        return { action: 'reconnect_database', retryAfter: 10000 };
      }
    });

    // Authentication recovery strategy
    this.recoveryStrategies.set('auth_error_recovery', {
      immediate: async (error, context) => {
        if (error.message.includes('token expired')) {
          return { action: 'refresh_token', retryAfter: 500 };
        }
        return { action: 'require_authentication', retryAfter: 0 };
      }
    });

    // Rate limit recovery strategy
    this.recoveryStrategies.set('rate_limit_recovery', {
      immediate: async (error, context) => {
        const retryAfter = this.extractRetryAfter(error) || 60000;
        return { action: 'backoff_retry', retryAfter };
      }
    });

    // Service discovery recovery strategy
    this.recoveryStrategies.set('service_discovery_recovery', {
      immediate: async (error, context) => {
        return { action: 'service_discovery_refresh', retryAfter: 2000 };
      },
      delayed: async (error, context) => {
        return { action: 'fallback_service', retryAfter: 5000 };
      }
    });

    // Validation recovery strategy
    this.recoveryStrategies.set('validation_error_recovery', {
      immediate: async (error, context) => {
        return {
          action: 'validation_guidance',
          guidance: this.extractValidationErrors(error),
          retryAfter: 0
        };
      }
    });
  }

  /**
   * Main error handling middleware
   */
  handleError() {
    return async (error, req, res, next) => {
      try {
        // Create error context
        const errorContext = {
          requestId: req.headers['x-request-id'] || this.generateRequestId(),
          method: req.method,
          path: req.path,
          userAgent: req.headers['user-agent'],
          ip: req.ip,
          timestamp: new Date(),
          error: {
            message: error.message,
            stack: error.stack,
            code: error.code,
            status: error.status || 500
          }
        };

        // Classify error
        const errorClassification = this.classifyError(error);

        // Get flow context for the request
        const flowContext = await this.getFlowContext(req, errorClassification);

        // Apply recovery strategy
        const recoveryResult = await this.applyRecoveryStrategy(
          error,
          errorClassification,
          { ...errorContext, req, res, flowContext }
        );

        // Log the error with flow context
        this.logErrorWithFlowContext(error, errorContext, errorClassification, recoveryResult);

        // Register the error pattern with Flow Registry
        await this.registerErrorPattern(error, errorClassification, flowContext);

        // Send response based on recovery strategy
        await this.sendErrorResponse(res, error, errorClassification, recoveryResult);

      } catch (handlerError) {
        this.logger.error('Error in FlowAwareErrorHandler', {
          originalError: error.message,
          handlerError: handlerError.message,
          stack: handlerError.stack
        });

        // Fallback to simple error response
        res.status(500).json({
          success: false,
          message: 'Internal server error',
          requestId: req.headers['x-request-id'] || this.generateRequestId(),
          timestamp: new Date()
        });
      }
    };
  }

  /**
   * Classify error based on patterns
   */
  classifyError(error) {
    const errorMessage = error.message || '';
    const errorCode = error.code || '';

    for (const [type, config] of this.errorPatterns.entries()) {
      for (const pattern of config.patterns) {
        if (pattern.test(errorMessage) || pattern.test(errorCode)) {
          return {
            type,
            flowType: config.flowType,
            severity: config.severity,
            category: config.category,
            confidence: 0.9
          };
        }
      }
    }

    // Default classification for unknown errors
    return {
      type: 'UNKNOWN_ERROR',
      flowType: 'generic_error_recovery',
      severity: 'medium',
      category: 'unknown',
      confidence: 0.5
    };
  }

  /**
   * Get flow context for the request
   */
  async getFlowContext(req, errorClassification) {
    try {
      // Try to get flow definition from Flow Registry
      const flows = await this.flowRegistryClient.listFlows({
        type: errorClassification.flowType,
        limit: 1
      });

      if (flows.data && flows.data.length > 0) {
        return {
          flowId: flows.data[0].id,
          flowName: flows.data[0].name,
          flowType: flows.data[0].type,
          recoverySteps: flows.data[0].nodes || []
        };
      }

      return null;
    } catch (error) {
      this.logger.warn('Failed to get flow context from Flow Registry', {
        error: error.message,
        errorType: errorClassification.type
      });
      return null;
    }
  }

  /**
   * Apply recovery strategy
   */
  async applyRecoveryStrategy(error, classification, context) {
    const strategy = this.recoveryStrategies.get(classification.flowType);

    if (!strategy) {
      return {
        action: 'log_and_respond',
        retryAfter: 0,
        success: false
      };
    }

    try {
      // Try immediate recovery first
      if (strategy.immediate) {
        const immediateResult = await strategy.immediate(error, context);
        if (immediateResult && immediateResult.action !== 'circuit_breaker') {
          return { ...immediateResult, success: true, strategy: 'immediate' };
        }
      }

      // Try delayed recovery if immediate fails
      if (strategy.delayed) {
        const delayedResult = await strategy.delayed(error, context);
        return { ...delayedResult, success: true, strategy: 'delayed' };
      }

      return {
        action: 'log_and_respond',
        retryAfter: 0,
        success: false,
        strategy: 'none'
      };
    } catch (recoveryError) {
      this.logger.error('Recovery strategy failed', {
        originalError: error.message,
        recoveryError: recoveryError.message,
        flowType: classification.flowType
      });

      return {
        action: 'log_and_respond',
        retryAfter: 0,
        success: false,
        strategy: 'failed'
      };
    }
  }

  /**
   * Register error pattern with Flow Registry
   */
  async registerErrorPattern(error, classification, flowContext) {
    try {
      const errorFlow = {
        name: `Error Pattern: ${classification.type}`,
        type: 'error_pattern',
        version: '1.0.0',
        description: `Automated error pattern registration for ${classification.type}`,
        nodes: [
          {
            id: 'error_detection',
            type: 'error_classifier',
            config: {
              errorType: classification.type,
              severity: classification.severity,
              category: classification.category,
              patterns: [error.message]
            }
          },
          {
            id: 'recovery_action',
            type: 'recovery_strategy',
            config: {
              flowType: classification.flowType,
              immediate: true,
              delayed: true
            }
          }
        ],
        edges: [
          {
            source: 'error_detection',
            target: 'recovery_action'
          }
        ],
        metadata: {
          autoGenerated: true,
          errorSample: error.message,
          timestamp: new Date()
        },
        createdBy: 'api-gateway-error-handler'
      };

      await this.flowRegistryClient.registerFlow(errorFlow);
    } catch (registrationError) {
      this.logger.warn('Failed to register error pattern with Flow Registry', {
        error: registrationError.message,
        errorType: classification.type
      });
    }
  }

  /**
   * Log error with flow context
   */
  logErrorWithFlowContext(error, context, classification, recoveryResult) {
    this.logger.error('Flow-aware error handled', {
      requestId: context.requestId,
      errorType: classification.type,
      severity: classification.severity,
      category: classification.category,
      flowType: classification.flowType,
      recoveryAction: recoveryResult.action,
      recoverySuccess: recoveryResult.success,
      retryAfter: recoveryResult.retryAfter,
      method: context.method,
      path: context.path,
      error: {
        message: error.message,
        code: error.code,
        status: error.status
      },
      timestamp: context.timestamp
    });
  }

  /**
   * Send error response
   */
  async sendErrorResponse(res, error, classification, recoveryResult) {
    const status = error.status || 500;
    const response = {
      success: false,
      error: {
        type: classification.type,
        message: error.message,
        severity: classification.severity,
        category: classification.category
      },
      recovery: {
        action: recoveryResult.action,
        retryAfter: recoveryResult.retryAfter,
        guidance: recoveryResult.guidance
      },
      timestamp: new Date(),
      requestId: res.locals.requestId || this.generateRequestId()
    };

    // Add specific headers based on recovery action
    switch (recoveryResult.action) {
      case 'retry_with_fallback':
        res.set('X-Retry-After', recoveryResult.retryAfter.toString());
        res.set('X-Fallback-Available', 'true');
        break;
      case 'backoff_retry':
        res.set('Retry-After', Math.ceil(recoveryResult.retryAfter / 1000).toString());
        break;
      case 'refresh_token':
        res.set('X-Auth-Action', 'refresh_required');
        break;
      case 'require_authentication':
        res.set('WWW-Authenticate', 'Bearer realm="api-gateway"');
        break;
    }

    res.status(status).json(response);
  }

  /**
   * Extract retry-after value from error
   */
  extractRetryAfter(error) {
    const retryMatch = error.message.match(/retry[- ]?after[:\s]*(\d+)/i);
    if (retryMatch) {
      return parseInt(retryMatch[1]) * 1000; // Convert to milliseconds
    }
    return null;
  }

  /**
   * Extract validation errors
   */
  extractValidationErrors(error) {
    // Try to parse structured validation errors
    if (error.details && Array.isArray(error.details)) {
      return error.details.map(detail => ({
        field: detail.path?.join('.'),
        message: detail.message,
        value: detail.context?.value
      }));
    }

    // Fallback to simple message parsing
    return [{
      message: error.message,
      suggestion: 'Please check your input data and try again'
    }];
  }

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Close the error handler and cleanup resources
   */
  async close() {
    if (this.flowRegistryClient) {
      this.flowRegistryClient.close();
    }
  }
}

module.exports = FlowAwareErrorHandler;