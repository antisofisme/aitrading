/**
 * @fileoverview ChainContext Manager for maintaining flow context across service boundaries
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Manages request flow context across microservice boundaries with automatic
 * propagation, state persistence, and distributed tracing capabilities.
 */

const { EventEmitter } = require('events');
const { performance } = require('perf_hooks');

// =============================================================================
// CHAIN CONTEXT CONSTANTS
// =============================================================================

const CONTEXT_STORAGE_KEY = 'chainContext';
const MAX_CONTEXT_SIZE = 1024 * 10; // 10KB max context size
const CONTEXT_TTL = 5 * 60 * 1000; // 5 minutes TTL
const MAX_NESTED_CALLS = 100;

// =============================================================================
// CHAIN CONTEXT CLASS
// =============================================================================

class ChainContext {
  constructor(options = {}) {
    this.id = options.id || require('uuid').v4();
    this.parentId = options.parentId || null;
    this.rootId = options.rootId || this.id;
    this.depth = options.depth || 0;
    this.serviceName = options.serviceName;
    this.startTime = options.startTime || performance.now();
    this.ttl = options.ttl || CONTEXT_TTL;
    this.createdAt = new Date();
    this.updatedAt = new Date();
    this.expiresAt = new Date(Date.now() + this.ttl);

    // Context data
    this.data = options.data || {};
    this.metadata = options.metadata || {};
    this.tags = options.tags || {};
    this.state = options.state || 'active';

    // Tracking information
    this.serviceChain = options.serviceChain || [];
    this.callStack = options.callStack || [];
    this.errors = options.errors || [];
    this.warnings = options.warnings || [];

    // Performance metrics
    this.metrics = {
      startTime: this.startTime,
      endTime: null,
      duration: null,
      cpuUsage: process.cpuUsage(),
      memoryUsage: process.memoryUsage(),
      operationCount: 0,
      errorCount: 0
    };

    // Validate nesting depth
    if (this.depth > MAX_NESTED_CALLS) {
      throw new Error(`Maximum nesting depth exceeded: ${this.depth}`);
    }
  }

  /**
   * Set context data with validation
   */
  set(key, value, options = {}) {
    if (this.isExpired()) {
      throw new Error('Cannot modify expired context');
    }

    const { ttl, persistent = false, encrypted = false } = options;

    this.data[key] = {
      value,
      setAt: new Date(),
      ttl,
      persistent,
      encrypted,
      serviceName: this.serviceName
    };

    this.updatedAt = new Date();
    this.validateSize();

    return this;
  }

  /**
   * Get context data
   */
  get(key, defaultValue = undefined) {
    const item = this.data[key];

    if (!item) {
      return defaultValue;
    }

    // Check item TTL
    if (item.ttl && Date.now() - item.setAt.getTime() > item.ttl) {
      delete this.data[key];
      return defaultValue;
    }

    return item.value;
  }

  /**
   * Add service to chain
   */
  addService(serviceName, operation = null) {
    const entry = {
      serviceName,
      operation,
      timestamp: performance.now(),
      depth: this.depth,
      parentService: this.serviceName
    };

    this.serviceChain.push(entry);
    this.callStack.push({
      service: serviceName,
      operation,
      startTime: performance.now(),
      endTime: null
    });

    this.metrics.operationCount++;
    this.updatedAt = new Date();
  }

  /**
   * Complete service operation
   */
  completeService(serviceName, operation = null, result = null) {
    const stackEntry = this.callStack
      .reverse()
      .find(entry => entry.service === serviceName && entry.operation === operation);

    if (stackEntry) {
      stackEntry.endTime = performance.now();
      stackEntry.duration = stackEntry.endTime - stackEntry.startTime;
      stackEntry.result = result;
    }

    this.updatedAt = new Date();
  }

  /**
   * Add error to context
   */
  addError(error, serviceName = null, operation = null) {
    const errorEntry = {
      message: error.message,
      code: error.code,
      stack: error.stack,
      serviceName: serviceName || this.serviceName,
      operation,
      timestamp: performance.now(),
      contextId: this.id
    };

    this.errors.push(errorEntry);
    this.metrics.errorCount++;
    this.updatedAt = new Date();

    // Mark context as failed if critical error
    if (error.critical) {
      this.state = 'failed';
    }
  }

  /**
   * Add warning to context
   */
  addWarning(message, serviceName = null, operation = null) {
    const warningEntry = {
      message,
      serviceName: serviceName || this.serviceName,
      operation,
      timestamp: performance.now(),
      contextId: this.id
    };

    this.warnings.push(warningEntry);
    this.updatedAt = new Date();
  }

  /**
   * Create child context
   */
  createChild(serviceName, options = {}) {
    return new ChainContext({
      parentId: this.id,
      rootId: this.rootId,
      depth: this.depth + 1,
      serviceName,
      ttl: options.ttl || this.ttl,
      data: options.inheritData ? { ...this.data } : {},
      metadata: options.inheritMetadata ? { ...this.metadata } : {},
      tags: options.inheritTags ? { ...this.tags } : {},
      ...options
    });
  }

  /**
   * Complete context
   */
  complete() {
    this.metrics.endTime = performance.now();
    this.metrics.duration = this.metrics.endTime - this.metrics.startTime;
    this.metrics.finalCpuUsage = process.cpuUsage(this.metrics.cpuUsage);
    this.metrics.finalMemoryUsage = process.memoryUsage();
    this.state = this.metrics.errorCount > 0 ? 'completed_with_errors' : 'completed';
    this.updatedAt = new Date();
  }

  /**
   * Check if context is expired
   */
  isExpired() {
    return Date.now() > this.expiresAt.getTime();
  }

  /**
   * Validate context size
   */
  validateSize() {
    const size = JSON.stringify(this).length;
    if (size > MAX_CONTEXT_SIZE) {
      throw new Error(`Context size exceeded limit: ${size} > ${MAX_CONTEXT_SIZE}`);
    }
  }

  /**
   * Serialize context for transmission
   */
  serialize(includeData = true) {
    const serialized = {
      id: this.id,
      parentId: this.parentId,
      rootId: this.rootId,
      depth: this.depth,
      serviceName: this.serviceName,
      startTime: this.startTime,
      ttl: this.ttl,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      expiresAt: this.expiresAt,
      state: this.state,
      serviceChain: this.serviceChain,
      metrics: this.metrics
    };

    if (includeData) {
      serialized.data = this.data;
      serialized.metadata = this.metadata;
      serialized.tags = this.tags;
    }

    return serialized;
  }

  /**
   * Deserialize context from data
   */
  static deserialize(data) {
    return new ChainContext({
      id: data.id,
      parentId: data.parentId,
      rootId: data.rootId,
      depth: data.depth,
      serviceName: data.serviceName,
      startTime: data.startTime,
      ttl: data.ttl,
      data: data.data || {},
      metadata: data.metadata || {},
      tags: data.tags || {},
      serviceChain: data.serviceChain || [],
      callStack: data.callStack || [],
      errors: data.errors || [],
      warnings: data.warnings || []
    });
  }
}

// =============================================================================
// CHAIN CONTEXT MANAGER CLASS
// =============================================================================

class ChainContextManager extends EventEmitter {
  constructor(options = {}) {
    super();

    this.serviceName = options.serviceName || 'unknown-service';
    this.logger = options.logger || console;
    this.storage = options.storage || new Map(); // In-memory by default
    this.enablePersistence = options.enablePersistence || false;
    this.enableDistributedTracing = options.enableDistributedTracing || false;
    this.cleanupInterval = options.cleanupInterval || 60000; // 1 minute
    this.maxContexts = options.maxContexts || 10000;

    // Start cleanup timer
    this.startCleanupTimer();

    // Bind methods
    this.middleware = this.middleware.bind(this);
  }

  /**
   * Express.js middleware
   */
  middleware(req, res, next) {
    try {
      const context = this.extractOrCreateContext(req);

      // Store context in request
      req[CONTEXT_STORAGE_KEY] = context;

      // Add current service to chain
      context.addService(this.serviceName, req.path);

      // Set response headers
      this.setResponseHeaders(res, context);

      // Override response.end to complete context
      this.wrapResponseEnd(req, res, context);

      // Emit context created event
      this.emit('contextCreated', context);

      next();

    } catch (error) {
      this.logger.error('ChainContextManager middleware error', {
        error: error.message,
        stack: error.stack,
        serviceName: this.serviceName
      });
      next(error);
    }
  }

  /**
   * Extract or create context from request
   */
  extractOrCreateContext(req) {
    const headers = req.headers;
    const contextData = headers['x-chain-context'];

    if (contextData) {
      try {
        const parsed = JSON.parse(contextData);
        const context = ChainContext.deserialize(parsed);
        context.serviceName = this.serviceName;
        return context;
      } catch (error) {
        this.logger.warn('Failed to parse chain context from headers', {
          error: error.message,
          contextData
        });
      }
    }

    // Create new context
    return new ChainContext({
      serviceName: this.serviceName,
      metadata: {
        requestPath: req.originalUrl,
        httpMethod: req.method,
        userAgent: headers['user-agent'],
        clientIp: req.ip
      },
      tags: {
        environment: process.env.NODE_ENV,
        version: process.env.SERVICE_VERSION
      }
    });
  }

  /**
   * Set response headers
   */
  setResponseHeaders(res, context) {
    const serialized = context.serialize(false);
    res.setHeader('x-chain-context', JSON.stringify(serialized));
    res.setHeader('x-context-id', context.id);
    res.setHeader('x-root-context-id', context.rootId);
    res.setHeader('x-service-chain', JSON.stringify(context.serviceChain.map(s => s.serviceName)));
  }

  /**
   * Wrap response.end to complete context
   */
  wrapResponseEnd(req, res, context) {
    const originalEnd = res.end;

    res.end = (...args) => {
      try {
        // Complete service operation
        context.completeService(this.serviceName, req.path, {
          statusCode: res.statusCode,
          responseSize: res.get('content-length')
        });

        // Complete context
        context.complete();

        // Store context if persistence enabled
        if (this.enablePersistence) {
          this.storeContext(context);
        }

        // Emit context completed event
        this.emit('contextCompleted', context);

      } catch (error) {
        this.logger.error('Error completing chain context', {
          error: error.message,
          contextId: context.id
        });
      }

      return originalEnd.apply(res, args);
    };
  }

  /**
   * Get context from request
   */
  getContext(req) {
    return req[CONTEXT_STORAGE_KEY] || null;
  }

  /**
   * Create child context for outgoing requests
   */
  createChildContext(req, targetService, options = {}) {
    const parentContext = this.getContext(req);

    if (!parentContext) {
      throw new Error('No parent context found');
    }

    const childContext = parentContext.createChild(targetService, options);

    // Store child context
    if (this.enablePersistence) {
      this.storeContext(childContext);
    }

    this.emit('childContextCreated', childContext, parentContext);

    return childContext;
  }

  /**
   * Get headers for outgoing requests
   */
  getOutgoingHeaders(req, targetService, options = {}) {
    const childContext = this.createChildContext(req, targetService, options);

    return {
      'x-chain-context': JSON.stringify(childContext.serialize()),
      'x-context-id': childContext.id,
      'x-parent-context-id': childContext.parentId,
      'x-root-context-id': childContext.rootId,
      'x-target-service': targetService
    };
  }

  /**
   * Store context in storage
   */
  storeContext(context) {
    if (this.storage.size >= this.maxContexts) {
      this.cleanupExpiredContexts();
    }

    this.storage.set(context.id, {
      context: context.serialize(),
      storedAt: Date.now()
    });
  }

  /**
   * Retrieve context from storage
   */
  getStoredContext(contextId) {
    const stored = this.storage.get(contextId);

    if (!stored) {
      return null;
    }

    try {
      return ChainContext.deserialize(stored.context);
    } catch (error) {
      this.logger.error('Failed to deserialize stored context', {
        contextId,
        error: error.message
      });
      this.storage.delete(contextId);
      return null;
    }
  }

  /**
   * Add error to context
   */
  addError(req, error, operation = null) {
    const context = this.getContext(req);

    if (context) {
      context.addError(error, this.serviceName, operation);
      this.emit('errorAdded', context, error);
    }
  }

  /**
   * Add warning to context
   */
  addWarning(req, message, operation = null) {
    const context = this.getContext(req);

    if (context) {
      context.addWarning(message, this.serviceName, operation);
      this.emit('warningAdded', context, message);
    }
  }

  /**
   * Get context metrics
   */
  getMetrics(req) {
    const context = this.getContext(req);
    return context ? context.metrics : null;
  }

  /**
   * Get service chain
   */
  getServiceChain(req) {
    const context = this.getContext(req);
    return context ? context.serviceChain : [];
  }

  /**
   * Start cleanup timer
   */
  startCleanupTimer() {
    this.cleanupTimer = setInterval(() => {
      this.cleanupExpiredContexts();
    }, this.cleanupInterval);
  }

  /**
   * Cleanup expired contexts
   */
  cleanupExpiredContexts() {
    const now = Date.now();
    let cleaned = 0;

    for (const [id, stored] of this.storage.entries()) {
      const context = ChainContext.deserialize(stored.context);

      if (context.isExpired()) {
        this.storage.delete(id);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      this.logger.debug('Cleaned up expired contexts', {
        cleaned,
        remaining: this.storage.size
      });
    }
  }

  /**
   * Stop manager and cleanup
   */
  stop() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.storage.clear();
    this.removeAllListeners();
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create ChainContextManager instance
 */
function createChainContextManager(options = {}) {
  return new ChainContextManager(options);
}

/**
 * Extract context ID from request
 */
function getContextId(req) {
  const context = req[CONTEXT_STORAGE_KEY];
  return context ? context.id : null;
}

/**
 * Check if request has chain context
 */
function hasChainContext(req) {
  return !!req[CONTEXT_STORAGE_KEY];
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  ChainContextManager,
  ChainContext,
  createChainContextManager,
  getContextId,
  hasChainContext,
  CONTEXT_STORAGE_KEY
};