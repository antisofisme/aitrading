/**
 * Flow Tracking Middleware for API Gateway
 * Integrates with Configuration Service Flow Registry for request tracing
 */

const { v4: uuidv4 } = require('uuid');
const axios = require('axios');
const winston = require('winston');

class FlowTrackingMiddleware {
  constructor(logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()]
    });

    this.configServiceUrl = process.env.CONFIG_SERVICE_URL || 'http://localhost:8012';
    this.flowTrackingEnabled = process.env.FLOW_TRACKING_ENABLED === 'true';
    this.maxTrackingDepth = parseInt(process.env.MAX_FLOW_TRACKING_DEPTH) || 10;

    // In-memory flow cache for performance
    this.flowCache = new Map();
    this.cacheTimeout = 300000; // 5 minutes
  }

  /**
   * Flow tracking middleware - adds request IDs and tracks flow
   */
  trackFlow = () => {
    return async (req, res, next) => {
      const startTime = Date.now();

      // Generate or extract flow ID
      const flowId = req.headers['x-flow-id'] || uuidv4();
      const requestId = req.headers['x-request-id'] || uuidv4();
      const parentFlowId = req.headers['x-parent-flow-id'];

      // Attach flow information to request
      req.flowId = flowId;
      req.requestId = requestId;
      req.parentFlowId = parentFlowId;
      req.flowDepth = parseInt(req.headers['x-flow-depth']) || 0;

      // Add flow headers to response
      res.setHeader('X-Flow-Id', flowId);
      res.setHeader('X-Request-Id', requestId);
      res.setHeader('X-Flow-Depth', req.flowDepth);

      // Track request start if flow tracking is enabled
      if (this.flowTrackingEnabled) {
        await this.trackRequestStart(req);
      }

      // Override res.json to track response
      const originalJson = res.json;
      res.json = (data) => {
        const endTime = Date.now();
        const duration = endTime - startTime;

        // Track request completion
        if (this.flowTrackingEnabled) {
          this.trackRequestEnd(req, res, duration, data).catch(error => {
            this.logger.error('Flow tracking error on completion', {
              error: error.message,
              flowId,
              requestId
            });
          });
        }

        // Log request completion
        this.logger.info('Request completed', {
          flowId,
          requestId,
          parentFlowId,
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          userId: req.user?.id,
          tenantId: req.user?.tenantId,
          userAgent: req.get('User-Agent')
        });

        return originalJson.call(this, data);
      };

      // Override res.send for non-JSON responses
      const originalSend = res.send;
      res.send = (data) => {
        const endTime = Date.now();
        const duration = endTime - startTime;

        if (this.flowTrackingEnabled) {
          this.trackRequestEnd(req, res, duration, data).catch(error => {
            this.logger.error('Flow tracking error on send', {
              error: error.message,
              flowId,
              requestId
            });
          });
        }

        return originalSend.call(this, data);
      };

      next();
    };
  };

  /**
   * Track request start in Flow Registry
   */
  async trackRequestStart(req) {
    try {
      const flowData = {
        flowId: req.flowId,
        requestId: req.requestId,
        parentFlowId: req.parentFlowId,
        depth: req.flowDepth,
        method: req.method,
        url: req.url,
        path: req.path,
        query: req.query,
        headers: this.sanitizeHeaders(req.headers),
        startTime: new Date().toISOString(),
        userId: req.user?.id,
        tenantId: req.user?.tenantId,
        userAgent: req.get('User-Agent'),
        ip: req.ip,
        status: 'started',
        service: 'api-gateway'
      };

      // Store in cache for quick access
      this.flowCache.set(req.requestId, {
        ...flowData,
        timestamp: Date.now()
      });

      // Send to Flow Registry asynchronously
      this.sendToFlowRegistry('start', flowData).catch(error => {
        this.logger.warn('Failed to send flow start to registry', {
          error: error.message,
          flowId: req.flowId,
          requestId: req.requestId
        });
      });

    } catch (error) {
      this.logger.error('Flow tracking start error', {
        error: error.message,
        flowId: req.flowId,
        requestId: req.requestId
      });
    }
  }

  /**
   * Track request completion in Flow Registry
   */
  async trackRequestEnd(req, res, duration, responseData) {
    try {
      const cachedFlow = this.flowCache.get(req.requestId);
      const flowData = {
        flowId: req.flowId,
        requestId: req.requestId,
        parentFlowId: req.parentFlowId,
        depth: req.flowDepth,
        endTime: new Date().toISOString(),
        duration,
        statusCode: res.statusCode,
        status: res.statusCode >= 400 ? 'error' : 'completed',
        responseSize: this.getResponseSize(responseData),
        error: res.statusCode >= 400 ? this.extractError(responseData) : null,
        service: 'api-gateway'
      };

      // Update cache
      if (cachedFlow) {
        this.flowCache.set(req.requestId, {
          ...cachedFlow,
          ...flowData,
          timestamp: Date.now()
        });
      }

      // Send to Flow Registry asynchronously
      this.sendToFlowRegistry('end', flowData).catch(error => {
        this.logger.warn('Failed to send flow end to registry', {
          error: error.message,
          flowId: req.flowId,
          requestId: req.requestId
        });
      });

      // Clean up cache entry after a delay
      setTimeout(() => {
        this.flowCache.delete(req.requestId);
      }, this.cacheTimeout);

    } catch (error) {
      this.logger.error('Flow tracking end error', {
        error: error.message,
        flowId: req.flowId,
        requestId: req.requestId
      });
    }
  }

  /**
   * Send flow data to Configuration Service Flow Registry
   */
  async sendToFlowRegistry(event, data) {
    try {
      const endpoint = `${this.configServiceUrl}/api/v1/flows/track`;

      await axios.post(endpoint, {
        event,
        data,
        timestamp: new Date().toISOString()
      }, {
        timeout: 2000, // Quick timeout to avoid blocking
        headers: {
          'Content-Type': 'application/json',
          'X-Service': 'api-gateway'
        }
      });

    } catch (error) {
      // Don't throw - flow tracking should not break the main request
      this.logger.debug('Flow registry request failed', {
        error: error.message,
        event,
        flowId: data.flowId
      });
    }
  }

  /**
   * Create downstream headers for service-to-service calls
   */
  createDownstreamHeaders(req, targetService) {
    const headers = {
      'X-Flow-Id': req.flowId,
      'X-Request-Id': uuidv4(), // New request ID for downstream call
      'X-Parent-Flow-Id': req.flowId,
      'X-Flow-Depth': req.flowDepth + 1,
      'X-Target-Service': targetService,
      'X-Source-Service': 'api-gateway'
    };

    // Pass through authentication headers
    if (req.headers['user-id']) headers['user-id'] = req.headers['user-id'];
    if (req.headers['tenant-id']) headers['tenant-id'] = req.headers['tenant-id'];
    if (req.headers['user-role']) headers['user-role'] = req.headers['user-role'];
    if (req.headers.authorization) headers.authorization = req.headers.authorization;

    return headers;
  }

  /**
   * Track downstream service call
   */
  async trackDownstreamCall(req, targetService, targetUrl, startTime) {
    if (!this.flowTrackingEnabled) return;

    try {
      const duration = Date.now() - startTime;
      const downstreamData = {
        flowId: req.flowId,
        parentRequestId: req.requestId,
        requestId: uuidv4(),
        targetService,
        targetUrl,
        startTime: new Date(startTime).toISOString(),
        endTime: new Date().toISOString(),
        duration,
        depth: req.flowDepth + 1,
        status: 'downstream_call'
      };

      await this.sendToFlowRegistry('downstream', downstreamData);

    } catch (error) {
      this.logger.debug('Downstream tracking failed', {
        error: error.message,
        targetService,
        flowId: req.flowId
      });
    }
  }

  /**
   * Get flow statistics from cache and registry
   */
  async getFlowStats() {
    try {
      // Get cache stats
      const cacheStats = {
        activeFlows: this.flowCache.size,
        flows: Array.from(this.flowCache.values()).map(flow => ({
          flowId: flow.flowId,
          requestId: flow.requestId,
          service: flow.service,
          status: flow.status,
          duration: flow.duration,
          timestamp: flow.timestamp
        }))
      };

      // Get registry stats
      let registryStats = {};
      try {
        const response = await axios.get(
          `${this.configServiceUrl}/api/v1/flows/statistics`,
          { timeout: 5000 }
        );
        registryStats = response.data;
      } catch (error) {
        this.logger.warn('Failed to get registry stats', {
          error: error.message
        });
      }

      return {
        cache: cacheStats,
        registry: registryStats,
        config: {
          enabled: this.flowTrackingEnabled,
          maxDepth: this.maxTrackingDepth,
          cacheTimeout: this.cacheTimeout
        }
      };

    } catch (error) {
      this.logger.error('Failed to get flow stats', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Sanitize headers for logging (remove sensitive data)
   */
  sanitizeHeaders(headers) {
    const sanitized = { ...headers };

    // Remove sensitive headers
    delete sanitized.authorization;
    delete sanitized.cookie;
    delete sanitized['x-api-key'];

    return sanitized;
  }

  /**
   * Get response size estimation
   */
  getResponseSize(data) {
    if (!data) return 0;
    if (typeof data === 'string') return data.length;
    if (typeof data === 'object') return JSON.stringify(data).length;
    return 0;
  }

  /**
   * Extract error information from response
   */
  extractError(responseData) {
    if (typeof responseData === 'object' && responseData.error) {
      return {
        message: responseData.error,
        code: responseData.code,
        details: responseData.message
      };
    }
    return null;
  }

  /**
   * Clean up old cache entries
   */
  cleanupCache() {
    const now = Date.now();
    let cleanedCount = 0;

    for (const [key, value] of this.flowCache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.flowCache.delete(key);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      this.logger.info('Flow cache cleanup completed', {
        cleanedEntries: cleanedCount,
        remainingEntries: this.flowCache.size
      });
    }

    return { cleanedEntries: cleanedCount, remainingEntries: this.flowCache.size };
  }

  /**
   * Get flow trace for debugging
   */
  getFlowTrace(flowId) {
    const traces = Array.from(this.flowCache.values())
      .filter(flow => flow.flowId === flowId)
      .sort((a, b) => a.timestamp - b.timestamp);

    return traces;
  }
}

module.exports = FlowTrackingMiddleware;