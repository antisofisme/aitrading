/**
 * @fileoverview Flow-aware middleware main entry point
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Main entry point for flow-aware middleware suite providing
 * request flow tracking, dependency analysis, and error correlation
 * across all microservices with <1ms performance overhead.
 */

// Core middleware components
const { FlowTracker, createFlowTracker, getFlowId, getCorrelationId, hasFlowContext, FLOW_HEADERS, FLOW_CONTEXT_KEY } = require('./FlowTracker');
const { ChainContextManager, ChainContext, createChainContextManager, getContextId, hasChainContext, CONTEXT_STORAGE_KEY } = require('./ChainContextManager');
const { FlowMetricsCollector, Metric, Timer, createFlowMetricsCollector, METRIC_TYPES, COLLECTION_INTERVALS, RETENTION_PERIODS } = require('./FlowMetricsCollector');
const { ChainEventPublisher, FlowEvent, EventChannel, WebhookChannel, LogChannel, MetricsChannel, createChainEventPublisher, EVENT_TYPES, EVENT_PRIORITIES, CHANNEL_TYPES } = require('./ChainEventPublisher');

// Integration utilities
const { ServiceIntegration, createServiceIntegration, setupFlowAwareMiddleware, MIDDLEWARE_CONFIG } = require('./ServiceIntegration');

// =============================================================================
// MAIN FLOW-AWARE MIDDLEWARE CLASS
// =============================================================================

class FlowAwareMiddleware {
  constructor(options = {}) {
    this.serviceName = options.serviceName || process.env.SERVICE_NAME || 'unknown-service';
    this.logger = options.logger || console;
    this.config = { ...MIDDLEWARE_CONFIG, ...options.config };

    // Initialize components
    this.components = {};
    this.initialized = false;
    this.performance = {
      setupTime: 0,
      requestCount: 0,
      avgOverhead: 0,
      maxOverhead: 0
    };
  }

  /**
   * Initialize flow-aware middleware
   */
  async initialize() {
    const startTime = performance.now();

    try {
      // Initialize metrics collector first
      if (this.config.metricsCollector.enabled) {
        this.components.metricsCollector = createFlowMetricsCollector({
          serviceName: this.serviceName,
          logger: this.logger,
          ...this.config.metricsCollector
        });
      }

      // Initialize event publisher
      if (this.config.eventPublisher.enabled) {
        this.components.eventPublisher = createChainEventPublisher({
          serviceName: this.serviceName,
          logger: this.logger,
          metricsCollector: this.components.metricsCollector,
          ...this.config.eventPublisher
        });
      }

      // Initialize flow tracker
      if (this.config.flowTracker.enabled) {
        this.components.flowTracker = createFlowTracker({
          serviceName: this.serviceName,
          logger: this.logger,
          metricsCollector: this.components.metricsCollector,
          eventPublisher: this.components.eventPublisher,
          ...this.config.flowTracker
        });
      }

      // Initialize chain context manager
      if (this.config.chainContext.enabled) {
        this.components.chainContextManager = createChainContextManager({
          serviceName: this.serviceName,
          logger: this.logger,
          ...this.config.chainContext
        });
      }

      // Setup integration hooks
      this.setupIntegrationHooks();

      this.performance.setupTime = performance.now() - startTime;
      this.initialized = true;

      this.logger.info('Flow-aware middleware initialized', {
        serviceName: this.serviceName,
        setupTime: this.performance.setupTime,
        components: Object.keys(this.components),
        performanceThreshold: this.config.flowTracker.performanceThreshold
      });

    } catch (error) {
      this.logger.error('Failed to initialize flow-aware middleware', {
        serviceName: this.serviceName,
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  /**
   * Setup integration hooks between components
   */
  setupIntegrationHooks() {
    const { metricsCollector, eventPublisher, chainContextManager } = this.components;

    // Connect metrics collector to event publisher
    if (metricsCollector && eventPublisher) {
      metricsCollector.on('metricsCollected', (data) => {
        eventPublisher.publish('metrics.collected', data, { priority: EVENT_PRIORITIES.LOW });
      });

      metricsCollector.on('realTimeMetrics', (metrics) => {
        eventPublisher.publish('metrics.realtime', metrics, { priority: EVENT_PRIORITIES.LOW });
      });
    }

    // Connect context manager to event publisher
    if (chainContextManager && eventPublisher) {
      chainContextManager.on('contextCreated', (context) => {
        eventPublisher.publishFlowStart(context);
      });

      chainContextManager.on('contextCompleted', (context) => {
        eventPublisher.publishFlowComplete(context);
      });

      chainContextManager.on('errorAdded', (context, error) => {
        eventPublisher.publishError(context, error);
      });
    }
  }

  /**
   * Get Express.js middleware function
   */
  middleware() {
    if (!this.initialized) {
      throw new Error('Flow-aware middleware not initialized. Call initialize() first.');
    }

    return (req, res, next) => {
      const requestStart = performance.now();

      try {
        // Apply flow tracker middleware
        if (this.components.flowTracker) {
          this.components.flowTracker.middleware(req, res, () => {});
        }

        // Apply chain context middleware
        if (this.components.chainContextManager) {
          this.components.chainContextManager.middleware(req, res, () => {});
        }

        // Track performance overhead
        const overhead = performance.now() - requestStart;
        this.updatePerformanceStats(overhead);

        // Validate performance threshold
        if (overhead > this.config.flowTracker.performanceThreshold) {
          this.logger.warn('Flow-aware middleware exceeded performance threshold', {
            overhead,
            threshold: this.config.flowTracker.performanceThreshold,
            serviceName: this.serviceName,
            path: req.path
          });

          // Publish performance alert
          if (this.components.eventPublisher) {
            this.components.eventPublisher.publishPerformanceAlert('threshold_exceeded', {
              overhead,
              threshold: this.config.flowTracker.performanceThreshold,
              path: req.path
            }, EVENT_PRIORITIES.HIGH);
          }
        }

        next();

      } catch (error) {
        this.logger.error('Flow-aware middleware error', {
          error: error.message,
          stack: error.stack,
          serviceName: this.serviceName,
          path: req.path
        });
        next(error);
      }
    };
  }

  /**
   * Update performance statistics
   */
  updatePerformanceStats(overhead) {
    this.performance.requestCount++;
    this.performance.avgOverhead = (
      (this.performance.avgOverhead * (this.performance.requestCount - 1) + overhead) /
      this.performance.requestCount
    );
    this.performance.maxOverhead = Math.max(this.performance.maxOverhead, overhead);
  }

  /**
   * Get flow context from request
   */
  getFlowContext(req) {
    return this.components.flowTracker ? this.components.flowTracker.getFlowContext(req) : null;
  }

  /**
   * Get chain context from request
   */
  getChainContext(req) {
    return this.components.chainContextManager ? this.components.chainContextManager.getContext(req) : null;
  }

  /**
   * Track dependency call
   */
  trackDependency(serviceName, type = 'http') {
    if (this.components.flowTracker) {
      return this.components.flowTracker.trackDependency(serviceName, type);
    }
    return (req, res, next) => next && next();
  }

  /**
   * Add error to flow context
   */
  addError(req, error, operation = null) {
    if (this.components.flowTracker) {
      this.components.flowTracker.addError(req, error);
    }
    if (this.components.chainContextManager) {
      this.components.chainContextManager.addError(req, error, operation);
    }
  }

  /**
   * Get headers for outgoing requests
   */
  getOutgoingHeaders(req, targetService) {
    const headers = {};

    if (this.components.flowTracker) {
      Object.assign(headers, this.components.flowTracker.createOutgoingHeaders(req, targetService));
    }

    if (this.components.chainContextManager) {
      Object.assign(headers, this.components.chainContextManager.getOutgoingHeaders(req, targetService));
    }

    return headers;
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return this.components.metricsCollector ? this.components.metricsCollector.getAllMetrics() : {};
  }

  /**
   * Get performance statistics
   */
  getPerformanceStats() {
    return {
      ...this.performance,
      meetsThreshold: this.performance.maxOverhead <= this.config.flowTracker.performanceThreshold,
      components: Object.keys(this.components).length,
      initialized: this.initialized
    };
  }

  /**
   * Get status information
   */
  getStatus() {
    return {
      serviceName: this.serviceName,
      initialized: this.initialized,
      components: {
        flowTracker: !!this.components.flowTracker,
        chainContextManager: !!this.components.chainContextManager,
        metricsCollector: !!this.components.metricsCollector,
        eventPublisher: !!this.components.eventPublisher
      },
      performance: this.getPerformanceStats(),
      config: this.config
    };
  }

  /**
   * Stop middleware and cleanup
   */
  async stop() {
    if (this.components.metricsCollector) {
      this.components.metricsCollector.stop();
    }

    if (this.components.eventPublisher) {
      await this.components.eventPublisher.stop();
    }

    if (this.components.chainContextManager) {
      this.components.chainContextManager.stop();
    }

    this.components = {};
    this.initialized = false;

    this.logger.info('Flow-aware middleware stopped', {
      serviceName: this.serviceName
    });
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create flow-aware middleware instance
 */
function createFlowAwareMiddleware(options = {}) {
  return new FlowAwareMiddleware(options);
}

/**
 * Quick setup for Express.js applications
 */
async function setupExpressMiddleware(app, options = {}) {
  const middleware = createFlowAwareMiddleware(options);
  await middleware.initialize();
  app.use(middleware.middleware());
  return middleware;
}

/**
 * Create HTTP client with flow tracking
 */
function createHttpClient(serviceName, middleware) {
  const axios = require('axios');

  const client = axios.create({
    timeout: 30000,
    headers: {
      'User-Agent': `${middleware.serviceName}-client/1.0`
    }
  });

  // Add request interceptor for flow tracking
  client.interceptors.request.use((config) => {
    // This would need request context to work properly
    // In practice, you'd use async local storage or similar
    return config;
  });

  return client;
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  // Main classes
  FlowAwareMiddleware,
  FlowTracker,
  ChainContextManager,
  FlowMetricsCollector,
  ChainEventPublisher,
  ServiceIntegration,

  // Context classes
  ChainContext,
  FlowEvent,
  Metric,
  Timer,

  // Channel classes
  EventChannel,
  WebhookChannel,
  LogChannel,
  MetricsChannel,

  // Factory functions
  createFlowAwareMiddleware,
  createFlowTracker,
  createChainContextManager,
  createFlowMetricsCollector,
  createChainEventPublisher,
  createServiceIntegration,

  // Utility functions
  setupExpressMiddleware,
  setupFlowAwareMiddleware,
  createHttpClient,
  getFlowId,
  getCorrelationId,
  getContextId,
  hasFlowContext,
  hasChainContext,

  // Constants
  FLOW_HEADERS,
  FLOW_CONTEXT_KEY,
  CONTEXT_STORAGE_KEY,
  EVENT_TYPES,
  EVENT_PRIORITIES,
  CHANNEL_TYPES,
  METRIC_TYPES,
  COLLECTION_INTERVALS,
  RETENTION_PERIODS,
  MIDDLEWARE_CONFIG
};