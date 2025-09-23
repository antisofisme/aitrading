/**
 * Flow-Aware Error Handler Middleware for API Gateway
 * Provides upstream/downstream impact analysis and Flow Registry integration
 */

const axios = require('axios');
const winston = require('winston');

class ErrorHandlerMiddleware {
  constructor(logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()]
    });

    this.configServiceUrl = process.env.CONFIG_SERVICE_URL || 'http://localhost:8012';
    this.chainDebugEnabled = process.env.CHAIN_DEBUG_ENABLED === 'true';

    // Error classification
    this.errorTypes = {
      AUTHENTICATION: 'authentication',
      AUTHORIZATION: 'authorization',
      VALIDATION: 'validation',
      RATE_LIMIT: 'rate_limit',
      UPSTREAM_ERROR: 'upstream_error',
      DOWNSTREAM_ERROR: 'downstream_error',
      SERVICE_UNAVAILABLE: 'service_unavailable',
      INTERNAL_ERROR: 'internal_error',
      FLOW_ERROR: 'flow_error'
    };

    // Impact levels
    this.impactLevels = {
      LOW: 'low',
      MEDIUM: 'medium',
      HIGH: 'high',
      CRITICAL: 'critical'
    };
  }

  /**
   * Main error handling middleware
   */
  handle = () => {
    return async (error, req, res, next) => {
      const startTime = Date.now();

      try {
        // Classify error
        const errorClassification = this.classifyError(error, req, res);

        // Analyze impact
        const impactAnalysis = await this.analyzeImpact(error, req, errorClassification);

        // Create error response
        const errorResponse = this.createErrorResponse(
          error,
          req,
          errorClassification,
          impactAnalysis
        );

        // Log error with flow context
        this.logError(error, req, errorClassification, impactAnalysis);

        // Track error in Flow Registry
        if (req.flowId) {
          await this.trackErrorInFlow(error, req, errorClassification, impactAnalysis);
        }

        // Send to Chain Debug System if enabled
        if (this.chainDebugEnabled) {
          this.sendToChainDebug(error, req, errorClassification, impactAnalysis)
            .catch(debugError => {
              this.logger.warn('Failed to send error to chain debug', {
                error: debugError.message,
                originalError: error.message
              });
            });
        }

        const processingTime = Date.now() - startTime;

        // Add processing time to response
        errorResponse.metadata = {
          ...errorResponse.metadata,
          errorProcessingTime: `${processingTime}ms`
        };

        // Set appropriate status code
        res.status(errorClassification.statusCode).json(errorResponse);

      } catch (handlerError) {
        // If error handler itself fails, send minimal response
        this.logger.error('Error handler failed', {
          handlerError: handlerError.message,
          originalError: error.message,
          flowId: req.flowId,
          requestId: req.requestId
        });

        res.status(500).json({
          error: 'Internal server error',
          message: 'An unexpected error occurred',
          code: 'ERROR_HANDLER_FAILED',
          timestamp: new Date().toISOString(),
          requestId: req.requestId
        });
      }
    };
  };

  /**
   * Classify error type and determine status code
   */
  classifyError(error, req, res) {
    let errorType = this.errorTypes.INTERNAL_ERROR;
    let statusCode = 500;
    let category = 'server';

    // Check error properties and context
    if (error.name === 'UnauthorizedError' || error.status === 401) {
      errorType = this.errorTypes.AUTHENTICATION;
      statusCode = 401;
      category = 'client';
    } else if (error.status === 403) {
      errorType = this.errorTypes.AUTHORIZATION;
      statusCode = 403;
      category = 'client';
    } else if (error.name === 'ValidationError' || error.status === 400) {
      errorType = this.errorTypes.VALIDATION;
      statusCode = 400;
      category = 'client';
    } else if (error.message && error.message.includes('rate limit')) {
      errorType = this.errorTypes.RATE_LIMIT;
      statusCode = 429;
      category = 'client';
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      errorType = this.errorTypes.SERVICE_UNAVAILABLE;
      statusCode = 503;
      category = 'infrastructure';
    } else if (error.response && error.response.status) {
      // Axios error from upstream service
      statusCode = error.response.status;
      if (statusCode >= 500) {
        errorType = this.errorTypes.UPSTREAM_ERROR;
        category = 'upstream';
      } else {
        errorType = this.errorTypes.DOWNSTREAM_ERROR;
        category = 'downstream';
      }
    } else if (req.flowId && error.message.includes('flow')) {
      errorType = this.errorTypes.FLOW_ERROR;
      statusCode = 500;
      category = 'flow';
    }

    return {
      type: errorType,
      statusCode,
      category,
      isClientError: statusCode >= 400 && statusCode < 500,
      isServerError: statusCode >= 500,
      isRetryable: this.isRetryable(errorType, statusCode)
    };
  }

  /**
   * Analyze upstream and downstream impact
   */
  async analyzeImpact(error, req, errorClassification) {
    const analysis = {
      level: this.impactLevels.LOW,
      affectedServices: [],
      upstreamImpact: false,
      downstreamImpact: false,
      flowDisruption: false,
      recommendations: []
    };

    try {
      // Determine impact level based on error type and service
      if (errorClassification.type === this.errorTypes.SERVICE_UNAVAILABLE) {
        analysis.level = this.impactLevels.HIGH;
        analysis.upstreamImpact = true;
        analysis.recommendations.push('Check service health and connectivity');
      }

      if (errorClassification.type === this.errorTypes.UPSTREAM_ERROR) {
        analysis.level = this.impactLevels.MEDIUM;
        analysis.upstreamImpact = true;
        analysis.recommendations.push('Investigate upstream service issues');
      }

      // Check if this is a critical service
      const targetService = this.extractTargetService(req);
      if (targetService && this.isCriticalService(targetService)) {
        analysis.level = this.impactLevels.CRITICAL;
        analysis.downstreamImpact = true;
        analysis.affectedServices.push(targetService);
      }

      // Check flow disruption
      if (req.flowId && errorClassification.category !== 'client') {
        analysis.flowDisruption = true;
        analysis.recommendations.push('Review flow execution chain');
      }

      // Check for cascading failures
      if (req.flowDepth > 3 && errorClassification.isServerError) {
        analysis.level = this.impactLevels.HIGH;
        analysis.recommendations.push('Potential cascading failure detected');
      }

      // Add retry recommendations
      if (errorClassification.isRetryable) {
        analysis.recommendations.push('Request can be safely retried');
      }

    } catch (analysisError) {
      this.logger.warn('Impact analysis failed', {
        error: analysisError.message,
        flowId: req.flowId
      });
    }

    return analysis;
  }

  /**
   * Create structured error response
   */
  createErrorResponse(error, req, classification, impact) {
    const response = {
      error: this.sanitizeErrorMessage(error.message || 'An error occurred'),
      code: error.code || classification.type.toUpperCase(),
      type: classification.type,
      category: classification.category,
      timestamp: new Date().toISOString(),
      requestId: req.requestId,
      flowId: req.flowId,
      metadata: {
        retryable: classification.isRetryable,
        impactLevel: impact.level,
        upstreamImpact: impact.upstreamImpact,
        downstreamImpact: impact.downstreamImpact,
        flowDisruption: impact.flowDisruption
      }
    };

    // Add recommendations for client errors
    if (classification.isClientError && impact.recommendations.length > 0) {
      response.recommendations = impact.recommendations;
    }

    // Add retry information for retryable errors
    if (classification.isRetryable) {
      response.retryAfter = this.calculateRetryAfter(classification.type);
    }

    // Add affected services for high impact errors
    if (impact.level === this.impactLevels.HIGH || impact.level === this.impactLevels.CRITICAL) {
      response.affectedServices = impact.affectedServices;
    }

    // Add debug information in development
    if (process.env.NODE_ENV === 'development') {
      response.debug = {
        stack: error.stack,
        originalError: error.toString(),
        requestPath: req.path,
        requestMethod: req.method,
        userAgent: req.get('User-Agent')
      };
    }

    return response;
  }

  /**
   * Log error with appropriate level and context
   */
  logError(error, req, classification, impact) {
    const logLevel = this.determineLogLevel(classification, impact);

    const logData = {
      error: error.message,
      stack: error.stack,
      type: classification.type,
      category: classification.category,
      statusCode: classification.statusCode,
      impactLevel: impact.level,
      flowId: req.flowId,
      requestId: req.requestId,
      userId: req.user?.id,
      tenantId: req.user?.tenantId,
      path: req.path,
      method: req.method,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      upstreamImpact: impact.upstreamImpact,
      downstreamImpact: impact.downstreamImpact,
      flowDisruption: impact.flowDisruption
    };

    this.logger[logLevel]('Request error', logData);
  }

  /**
   * Track error in Flow Registry
   */
  async trackErrorInFlow(error, req, classification, impact) {
    try {
      const errorData = {
        flowId: req.flowId,
        requestId: req.requestId,
        errorType: classification.type,
        errorCategory: classification.category,
        statusCode: classification.statusCode,
        errorMessage: error.message,
        impactLevel: impact.level,
        upstreamImpact: impact.upstreamImpact,
        downstreamImpact: impact.downstreamImpact,
        flowDisruption: impact.flowDisruption,
        timestamp: new Date().toISOString(),
        service: 'api-gateway'
      };

      await axios.post(
        `${this.configServiceUrl}/api/v1/flows/error`,
        errorData,
        {
          timeout: 2000,
          headers: { 'Content-Type': 'application/json' }
        }
      );

    } catch (trackingError) {
      this.logger.debug('Failed to track error in flow registry', {
        error: trackingError.message,
        flowId: req.flowId
      });
    }
  }

  /**
   * Send error to Chain Debug System
   */
  async sendToChainDebug(error, req, classification, impact) {
    try {
      const debugData = {
        type: 'api_gateway_error',
        flowId: req.flowId,
        requestId: req.requestId,
        error: {
          message: error.message,
          stack: error.stack,
          type: classification.type,
          category: classification.category,
          statusCode: classification.statusCode
        },
        impact,
        context: {
          path: req.path,
          method: req.method,
          userId: req.user?.id,
          tenantId: req.user?.tenantId,
          timestamp: new Date().toISOString()
        }
      };

      const chainDebugUrl = process.env.CHAIN_DEBUG_URL || 'http://localhost:8030';

      await axios.post(
        `${chainDebugUrl}/api/debug/error`,
        debugData,
        {
          timeout: 3000,
          headers: { 'Content-Type': 'application/json' }
        }
      );

    } catch (debugError) {
      // Don't throw - debug tracking is optional
      this.logger.debug('Chain debug tracking failed', {
        error: debugError.message
      });
    }
  }

  /**
   * Helper methods
   */
  isRetryable(errorType, statusCode) {
    const retryableTypes = [
      this.errorTypes.SERVICE_UNAVAILABLE,
      this.errorTypes.UPSTREAM_ERROR
    ];

    const retryableStatusCodes = [408, 429, 502, 503, 504];

    return retryableTypes.includes(errorType) || retryableStatusCodes.includes(statusCode);
  }

  calculateRetryAfter(errorType) {
    switch (errorType) {
      case this.errorTypes.RATE_LIMIT:
        return 60; // 1 minute
      case this.errorTypes.SERVICE_UNAVAILABLE:
        return 30; // 30 seconds
      default:
        return 5; // 5 seconds
    }
  }

  extractTargetService(req) {
    // Extract target service from request path
    const pathParts = req.path.split('/');
    if (pathParts.length >= 3 && pathParts[1] === 'api') {
      return pathParts[2];
    }
    return null;
  }

  isCriticalService(serviceName) {
    const criticalServices = [
      'trading',
      'orders',
      'portfolio',
      'config',
      'users',
      'payments'
    ];
    return criticalServices.includes(serviceName);
  }

  determineLogLevel(classification, impact) {
    if (impact.level === this.impactLevels.CRITICAL) return 'error';
    if (impact.level === this.impactLevels.HIGH) return 'error';
    if (impact.level === this.impactLevels.MEDIUM) return 'warn';
    if (classification.isServerError) return 'error';
    if (classification.statusCode === 401 || classification.statusCode === 403) return 'warn';
    return 'info';
  }

  sanitizeErrorMessage(message) {
    // Remove sensitive information from error messages
    return message
      .replace(/password[=:]\s*[^\s,}]+/gi, 'password=***')
      .replace(/token[=:]\s*[^\s,}]+/gi, 'token=***')
      .replace(/key[=:]\s*[^\s,}]+/gi, 'key=***')
      .replace(/secret[=:]\s*[^\s,}]+/gi, 'secret=***');
  }

  /**
   * Get error statistics
   */
  getErrorStats() {
    // This would typically query a database or metrics system
    // For now, return a placeholder
    return {
      message: 'Error statistics would be retrieved from monitoring system',
      note: 'Implement with actual metrics collection'
    };
  }
}

module.exports = ErrorHandlerMiddleware;