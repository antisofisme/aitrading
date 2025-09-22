/**
 * @fileoverview FlowTracker Middleware for Express.js Request Flow Tracking
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Provides unique flow IDs for end-to-end tracking across microservices
 * with <1ms performance overhead and automatic dependency detection.
 */

const { v4: uuidv4 } = require('uuid');
const { performance } = require('perf_hooks');

// =============================================================================
// FLOW TRACKER CONSTANTS
// =============================================================================

const FLOW_HEADERS = {
  FLOW_ID: 'x-flow-id',
  PARENT_FLOW: 'x-parent-flow-id',
  SERVICE_CHAIN: 'x-service-chain',
  REQUEST_START: 'x-request-start',
  CORRELATION_ID: 'x-correlation-id',
  USER_ID: 'x-user-id',
  SESSION_ID: 'x-session-id'
};

const FLOW_CONTEXT_KEY = 'flowContext';
const MAX_CHAIN_LENGTH = 50; // Prevent infinite chains
const PERFORMANCE_THRESHOLD = 1; // 1ms overhead limit

// =============================================================================
// FLOW CONTEXT CLASS
// =============================================================================

class FlowContext {
  constructor(options = {}) {
    this.flowId = options.flowId || uuidv4();
    this.parentFlowId = options.parentFlowId || null;
    this.correlationId = options.correlationId || uuidv4();
    this.serviceName = options.serviceName;
    this.serviceChain = options.serviceChain || [];
    this.requestStart = options.requestStart || performance.now();
    this.userId = options.userId || null;
    this.sessionId = options.sessionId || null;
    this.tags = options.tags || {};
    this.metadata = options.metadata || {};
    this.dependencies = new Set();
    this.errors = [];
    this.metrics = {
      startTime: this.requestStart,
      endTime: null,
      duration: null,
      memoryUsage: process.memoryUsage(),
      cpuUsage: process.cpuUsage()
    };
  }

  /**
   * Add service to chain with validation
   */
  addToChain(serviceName) {
    if (this.serviceChain.length >= MAX_CHAIN_LENGTH) {
      throw new Error(`Service chain exceeded maximum length of ${MAX_CHAIN_LENGTH}`);
    }

    if (!this.serviceChain.includes(serviceName)) {
      this.serviceChain.push(serviceName);
    }
  }

  /**
   * Add dependency tracking
   */
  addDependency(serviceName, type = 'http') {
    this.dependencies.add({
      service: serviceName,
      type,
      timestamp: performance.now(),
      flowId: this.flowId
    });
  }

  /**
   * Add error to flow context
   */
  addError(error, serviceName = null) {
    this.errors.push({
      message: error.message,
      stack: error.stack,
      code: error.code,
      service: serviceName || this.serviceName,
      timestamp: performance.now(),
      flowId: this.flowId
    });
  }

  /**
   * Complete flow tracking
   */
  complete() {
    this.metrics.endTime = performance.now();
    this.metrics.duration = this.metrics.endTime - this.metrics.startTime;
    this.metrics.finalMemoryUsage = process.memoryUsage();
    this.metrics.finalCpuUsage = process.cpuUsage(this.metrics.cpuUsage);
  }

  /**
   * Get serializable context for headers
   */
  toHeaders() {
    return {
      [FLOW_HEADERS.FLOW_ID]: this.flowId,
      [FLOW_HEADERS.PARENT_FLOW]: this.parentFlowId,
      [FLOW_HEADERS.CORRELATION_ID]: this.correlationId,
      [FLOW_HEADERS.SERVICE_CHAIN]: JSON.stringify(this.serviceChain),
      [FLOW_HEADERS.REQUEST_START]: this.requestStart.toString(),
      [FLOW_HEADERS.USER_ID]: this.userId,
      [FLOW_HEADERS.SESSION_ID]: this.sessionId
    };
  }

  /**
   * Create context from headers
   */
  static fromHeaders(headers, serviceName) {
    return new FlowContext({
      flowId: headers[FLOW_HEADERS.FLOW_ID],
      parentFlowId: headers[FLOW_HEADERS.PARENT_FLOW],
      correlationId: headers[FLOW_HEADERS.CORRELATION_ID],
      serviceName,
      serviceChain: headers[FLOW_HEADERS.SERVICE_CHAIN]
        ? JSON.parse(headers[FLOW_HEADERS.SERVICE_CHAIN])
        : [],
      requestStart: headers[FLOW_HEADERS.REQUEST_START]
        ? parseFloat(headers[FLOW_HEADERS.REQUEST_START])
        : performance.now(),
      userId: headers[FLOW_HEADERS.USER_ID],
      sessionId: headers[FLOW_HEADERS.SESSION_ID]
    });
  }
}

// =============================================================================
// FLOW TRACKER MIDDLEWARE
// =============================================================================

class FlowTracker {
  constructor(options = {}) {
    this.serviceName = options.serviceName || 'unknown-service';
    this.logger = options.logger || console;
    this.metricsCollector = options.metricsCollector || null;
    this.eventPublisher = options.eventPublisher || null;
    this.enablePerformanceTracking = options.enablePerformanceTracking !== false;
    this.enableDependencyTracking = options.enableDependencyTracking !== false;
    this.performanceThreshold = options.performanceThreshold || PERFORMANCE_THRESHOLD;

    // Bind methods
    this.middleware = this.middleware.bind(this);
    this.trackDependency = this.trackDependency.bind(this);
    this.getFlowContext = this.getFlowContext.bind(this);
  }

  /**
   * Express.js middleware function
   */
  middleware(req, res, next) {
    const startTime = performance.now();

    try {
      // Create or extract flow context
      const flowContext = this.createFlowContext(req);

      // Attach to request
      req[FLOW_CONTEXT_KEY] = flowContext;

      // Add service to chain
      flowContext.addToChain(this.serviceName);

      // Set response headers
      this.setResponseHeaders(res, flowContext);

      // Track request start
      this.trackRequestStart(req, flowContext);

      // Override end to capture completion
      this.wrapResponseEnd(req, res, flowContext);

      // Performance validation
      const setupTime = performance.now() - startTime;
      if (setupTime > this.performanceThreshold) {
        this.logger.warn('FlowTracker middleware exceeded performance threshold', {
          setupTime,
          threshold: this.performanceThreshold,
          flowId: flowContext.flowId
        });
      }

      next();

    } catch (error) {
      this.logger.error('FlowTracker middleware error', {
        error: error.message,
        stack: error.stack,
        serviceName: this.serviceName
      });
      next(error);
    }
  }

  /**
   * Create flow context from request
   */
  createFlowContext(req) {
    const headers = req.headers;

    // Check if flow already exists
    if (headers[FLOW_HEADERS.FLOW_ID]) {
      return FlowContext.fromHeaders(headers, this.serviceName);
    }

    // Create new flow context
    return new FlowContext({
      serviceName: this.serviceName,
      userId: this.extractUserId(req),
      sessionId: this.extractSessionId(req),
      tags: {
        method: req.method,
        path: req.path,
        userAgent: headers['user-agent'],
        clientIp: req.ip || req.connection.remoteAddress
      },
      metadata: {
        requestPath: req.originalUrl,
        httpMethod: req.method,
        userAgent: headers['user-agent']
      }
    });
  }

  /**
   * Set response headers for flow tracking
   */
  setResponseHeaders(res, flowContext) {
    const headers = flowContext.toHeaders();

    Object.entries(headers).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        res.setHeader(key, value);
      }
    });
  }

  /**
   * Track request start event
   */
  trackRequestStart(req, flowContext) {
    if (this.eventPublisher) {
      this.eventPublisher.publish('flow.request.start', {
        flowId: flowContext.flowId,
        correlationId: flowContext.correlationId,
        serviceName: this.serviceName,
        method: req.method,
        path: req.path,
        timestamp: flowContext.requestStart,
        serviceChain: flowContext.serviceChain,
        userId: flowContext.userId,
        sessionId: flowContext.sessionId
      });
    }
  }

  /**
   * Wrap response.end to capture completion
   */
  wrapResponseEnd(req, res, flowContext) {
    const originalEnd = res.end;

    res.end = (...args) => {
      try {
        // Complete flow tracking
        flowContext.complete();

        // Track request completion
        this.trackRequestComplete(req, res, flowContext);

        // Collect metrics
        if (this.metricsCollector) {
          this.metricsCollector.collect(flowContext);
        }

        // Publish completion event
        if (this.eventPublisher) {
          this.eventPublisher.publish('flow.request.complete', {
            flowId: flowContext.flowId,
            correlationId: flowContext.correlationId,
            serviceName: this.serviceName,
            statusCode: res.statusCode,
            duration: flowContext.metrics.duration,
            serviceChain: flowContext.serviceChain,
            dependencies: Array.from(flowContext.dependencies),
            errors: flowContext.errors,
            timestamp: flowContext.metrics.endTime
          });
        }

      } catch (error) {
        this.logger.error('Error in FlowTracker response.end wrapper', {
          error: error.message,
          flowId: flowContext.flowId
        });
      }

      // Call original end
      return originalEnd.apply(res, args);
    };
  }

  /**
   * Track request completion
   */
  trackRequestComplete(req, res, flowContext) {
    this.logger.info('Request flow completed', {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      serviceName: this.serviceName,
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: flowContext.metrics.duration,
      serviceChain: flowContext.serviceChain,
      dependencyCount: flowContext.dependencies.size,
      errorCount: flowContext.errors.length,
      userId: flowContext.userId,
      sessionId: flowContext.sessionId
    });
  }

  /**
   * Track service dependency
   */
  trackDependency(serviceName, type = 'http') {
    return (req, res, next) => {
      const flowContext = req[FLOW_CONTEXT_KEY];

      if (flowContext && this.enableDependencyTracking) {
        flowContext.addDependency(serviceName, type);

        if (this.eventPublisher) {
          this.eventPublisher.publish('flow.dependency.called', {
            flowId: flowContext.flowId,
            correlationId: flowContext.correlationId,
            fromService: this.serviceName,
            toService: serviceName,
            dependencyType: type,
            timestamp: performance.now()
          });
        }
      }

      if (next) next();
    };
  }

  /**
   * Get flow context from request
   */
  getFlowContext(req) {
    return req[FLOW_CONTEXT_KEY] || null;
  }

  /**
   * Add error to flow context
   */
  addError(req, error) {
    const flowContext = req[FLOW_CONTEXT_KEY];

    if (flowContext) {
      flowContext.addError(error, this.serviceName);

      if (this.eventPublisher) {
        this.eventPublisher.publish('flow.error.occurred', {
          flowId: flowContext.flowId,
          correlationId: flowContext.correlationId,
          serviceName: this.serviceName,
          error: {
            message: error.message,
            code: error.code,
            stack: error.stack
          },
          timestamp: performance.now()
        });
      }
    }
  }

  /**
   * Extract user ID from request
   */
  extractUserId(req) {
    return req.user?.id || req.headers['x-user-id'] || null;
  }

  /**
   * Extract session ID from request
   */
  extractSessionId(req) {
    return req.sessionID || req.headers['x-session-id'] || null;
  }

  /**
   * Create headers for outgoing requests
   */
  createOutgoingHeaders(req, targetService) {
    const flowContext = req[FLOW_CONTEXT_KEY];

    if (!flowContext) {
      return {};
    }

    // Track dependency
    flowContext.addDependency(targetService, 'http');

    return flowContext.toHeaders();
  }

  /**
   * Get flow metrics
   */
  getFlowMetrics(req) {
    const flowContext = req[FLOW_CONTEXT_KEY];
    return flowContext ? flowContext.metrics : null;
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create FlowTracker middleware instance
 */
function createFlowTracker(options = {}) {
  return new FlowTracker(options);
}

/**
 * Extract flow ID from request
 */
function getFlowId(req) {
  const flowContext = req[FLOW_CONTEXT_KEY];
  return flowContext ? flowContext.flowId : null;
}

/**
 * Extract correlation ID from request
 */
function getCorrelationId(req) {
  const flowContext = req[FLOW_CONTEXT_KEY];
  return flowContext ? flowContext.correlationId : null;
}

/**
 * Check if request has flow context
 */
function hasFlowContext(req) {
  return !!req[FLOW_CONTEXT_KEY];
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  FlowTracker,
  FlowContext,
  createFlowTracker,
  getFlowId,
  getCorrelationId,
  hasFlowContext,
  FLOW_HEADERS,
  FLOW_CONTEXT_KEY
};