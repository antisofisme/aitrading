/**
 * @fileoverview Chain Event Publisher for flow events monitoring
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Publishes flow events for monitoring, alerting, and analytics with
 * real-time streaming, event correlation, and multi-channel distribution.
 */

const { EventEmitter } = require('events');
const { performance } = require('perf_hooks');

// =============================================================================
// EVENT CONSTANTS
// =============================================================================

const EVENT_TYPES = {
  FLOW_START: 'flow.start',
  FLOW_COMPLETE: 'flow.complete',
  FLOW_ERROR: 'flow.error',
  SERVICE_CALL: 'service.call',
  SERVICE_RESPONSE: 'service.response',
  DEPENDENCY_CALL: 'dependency.call',
  DEPENDENCY_RESPONSE: 'dependency.response',
  ERROR_OCCURRED: 'error.occurred',
  WARNING_ISSUED: 'warning.issued',
  PERFORMANCE_ALERT: 'performance.alert',
  THRESHOLD_EXCEEDED: 'threshold.exceeded'
};

const EVENT_PRIORITIES = {
  LOW: 1,
  NORMAL: 2,
  HIGH: 3,
  CRITICAL: 4,
  EMERGENCY: 5
};

const CHANNEL_TYPES = {
  WEBHOOK: 'webhook',
  SSE: 'sse',
  WEBSOCKET: 'websocket',
  QUEUE: 'queue',
  LOG: 'log',
  METRICS: 'metrics'
};

// =============================================================================
// EVENT CLASSES
// =============================================================================

class FlowEvent {
  constructor(type, data, options = {}) {
    this.id = options.id || require('uuid').v4();
    this.type = type;
    this.data = data;
    this.timestamp = options.timestamp || Date.now();
    this.priority = options.priority || EVENT_PRIORITIES.NORMAL;
    this.serviceName = options.serviceName;
    this.flowId = options.flowId;
    this.correlationId = options.correlationId;
    this.tags = options.tags || {};
    this.metadata = options.metadata || {};
    this.source = options.source || 'flow-tracker';
    this.version = options.version || '1.0';
    this.retryCount = 0;
    this.maxRetries = options.maxRetries || 3;
  }

  /**
   * Serialize event for transmission
   */
  serialize() {
    return {
      id: this.id,
      type: this.type,
      data: this.data,
      timestamp: this.timestamp,
      priority: this.priority,
      serviceName: this.serviceName,
      flowId: this.flowId,
      correlationId: this.correlationId,
      tags: this.tags,
      metadata: this.metadata,
      source: this.source,
      version: this.version
    };
  }

  /**
   * Create event from serialized data
   */
  static deserialize(data) {
    return new FlowEvent(data.type, data.data, {
      id: data.id,
      timestamp: data.timestamp,
      priority: data.priority,
      serviceName: data.serviceName,
      flowId: data.flowId,
      correlationId: data.correlationId,
      tags: data.tags,
      metadata: data.metadata,
      source: data.source,
      version: data.version
    });
  }
}

class EventChannel {
  constructor(type, config = {}) {
    this.type = type;
    this.config = config;
    this.enabled = config.enabled !== false;
    this.filters = config.filters || [];
    this.rateLimits = config.rateLimits || {};
    this.buffer = [];
    this.bufferSize = config.bufferSize || 1000;
    this.batchSize = config.batchSize || 10;
    this.flushInterval = config.flushInterval || 5000;
    this.lastFlush = Date.now();
    this.eventCount = 0;
    this.errorCount = 0;
  }

  /**
   * Check if event should be published to this channel
   */
  shouldPublish(event) {
    if (!this.enabled) return false;

    // Apply filters
    for (const filter of this.filters) {
      if (!this.applyFilter(filter, event)) {
        return false;
      }
    }

    // Check rate limits
    if (this.rateLimits.maxEventsPerSecond) {
      const now = Date.now();
      const elapsed = now - (this.lastRateCheck || now);
      if (elapsed < 1000 && this.recentEventCount >= this.rateLimits.maxEventsPerSecond) {
        return false;
      }

      if (elapsed >= 1000) {
        this.lastRateCheck = now;
        this.recentEventCount = 0;
      }

      this.recentEventCount = (this.recentEventCount || 0) + 1;
    }

    return true;
  }

  /**
   * Apply filter to event
   */
  applyFilter(filter, event) {
    switch (filter.type) {
      case 'priority':
        return event.priority >= (filter.minPriority || EVENT_PRIORITIES.LOW);

      case 'eventType':
        return filter.include
          ? filter.include.includes(event.type)
          : !filter.exclude?.includes(event.type);

      case 'service':
        return filter.services
          ? filter.services.includes(event.serviceName)
          : true;

      case 'tag':
        return filter.tags
          ? filter.tags.every(tag => event.tags[tag.key] === tag.value)
          : true;

      default:
        return true;
    }
  }

  /**
   * Add event to buffer
   */
  addEvent(event) {
    if (this.buffer.length >= this.bufferSize) {
      this.buffer.shift(); // Remove oldest event
    }

    this.buffer.push(event);
    this.eventCount++;

    // Check if should flush
    if (this.buffer.length >= this.batchSize ||
        Date.now() - this.lastFlush >= this.flushInterval) {
      this.flush();
    }
  }

  /**
   * Flush events from buffer
   */
  async flush() {
    if (this.buffer.length === 0) return;

    const events = this.buffer.splice(0, this.batchSize);
    this.lastFlush = Date.now();

    try {
      await this.publish(events);
    } catch (error) {
      this.errorCount++;
      // Re-add events to buffer for retry
      this.buffer.unshift(...events);
      throw error;
    }
  }

  /**
   * Publish events (to be implemented by specific channel types)
   */
  async publish(events) {
    throw new Error('publish method must be implemented by channel subclass');
  }
}

class WebhookChannel extends EventChannel {
  constructor(config) {
    super(CHANNEL_TYPES.WEBHOOK, config);
    this.url = config.url;
    this.headers = config.headers || {};
    this.timeout = config.timeout || 5000;
  }

  async publish(events) {
    const fetch = require('node-fetch');

    const payload = {
      events: events.map(event => event.serialize()),
      timestamp: Date.now(),
      batchId: require('uuid').v4()
    };

    const response = await fetch(this.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.headers
      },
      body: JSON.stringify(payload),
      timeout: this.timeout
    });

    if (!response.ok) {
      throw new Error(`Webhook failed: ${response.status} ${response.statusText}`);
    }
  }
}

class LogChannel extends EventChannel {
  constructor(config) {
    super(CHANNEL_TYPES.LOG, config);
    this.logger = config.logger || console;
    this.logLevel = config.logLevel || 'info';
  }

  async publish(events) {
    for (const event of events) {
      const logData = {
        eventId: event.id,
        eventType: event.type,
        flowId: event.flowId,
        correlationId: event.correlationId,
        serviceName: event.serviceName,
        timestamp: new Date(event.timestamp).toISOString(),
        priority: event.priority,
        data: event.data,
        tags: event.tags
      };

      const logMethod = this.getLogMethod(event.priority);
      this.logger[logMethod]('Flow event published', logData);
    }
  }

  getLogMethod(priority) {
    switch (priority) {
      case EVENT_PRIORITIES.EMERGENCY:
      case EVENT_PRIORITIES.CRITICAL:
        return 'error';
      case EVENT_PRIORITIES.HIGH:
        return 'warn';
      case EVENT_PRIORITIES.NORMAL:
        return 'info';
      case EVENT_PRIORITIES.LOW:
      default:
        return 'debug';
    }
  }
}

class MetricsChannel extends EventChannel {
  constructor(config) {
    super(CHANNEL_TYPES.METRICS, config);
    this.metricsCollector = config.metricsCollector;
  }

  async publish(events) {
    if (!this.metricsCollector) return;

    for (const event of events) {
      // Increment event counter
      this.metricsCollector.incrementCounter('flow_events_published_total', 1, {
        event_type: event.type,
        service: event.serviceName,
        priority: event.priority.toString()
      });

      // Record event processing time if available
      if (event.data.duration) {
        this.metricsCollector.recordTimer('flow_event_duration_seconds', event.data.duration, {
          event_type: event.type,
          service: event.serviceName
        });
      }
    }
  }
}

// =============================================================================
// CHAIN EVENT PUBLISHER CLASS
// =============================================================================

class ChainEventPublisher extends EventEmitter {
  constructor(options = {}) {
    super();

    this.serviceName = options.serviceName || 'unknown-service';
    this.logger = options.logger || console;
    this.enableBuffering = options.enableBuffering !== false;
    this.enableRetries = options.enableRetries !== false;
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.flushInterval = options.flushInterval || 5000;

    // Event channels
    this.channels = new Map();
    this.eventBuffer = [];
    this.eventHistory = new Map();
    this.correlationMap = new Map();

    // Statistics
    this.stats = {
      eventsPublished: 0,
      eventsDropped: 0,
      channelErrors: 0,
      retriesAttempted: 0
    };

    // Start flush timer
    this.startFlushTimer();

    // Initialize default channels
    this.initializeDefaultChannels(options);
  }

  /**
   * Initialize default channels
   */
  initializeDefaultChannels(options) {
    // Log channel (always enabled)
    this.addChannel('default-log', new LogChannel({
      logger: this.logger,
      logLevel: options.logLevel || 'info'
    }));

    // Metrics channel if collector provided
    if (options.metricsCollector) {
      this.addChannel('default-metrics', new MetricsChannel({
        metricsCollector: options.metricsCollector
      }));
    }

    // Webhook channel if configured
    if (options.webhookUrl) {
      this.addChannel('default-webhook', new WebhookChannel({
        url: options.webhookUrl,
        headers: options.webhookHeaders,
        timeout: options.webhookTimeout
      }));
    }
  }

  /**
   * Add event channel
   */
  addChannel(name, channel) {
    this.channels.set(name, channel);
    this.logger.debug('Event channel added', { channelName: name, channelType: channel.type });
  }

  /**
   * Remove event channel
   */
  removeChannel(name) {
    const channel = this.channels.get(name);
    if (channel) {
      this.channels.delete(name);
      this.logger.debug('Event channel removed', { channelName: name });
    }
  }

  /**
   * Publish flow event
   */
  async publish(eventType, data, options = {}) {
    try {
      const event = new FlowEvent(eventType, data, {
        serviceName: this.serviceName,
        ...options
      });

      // Add to event history
      this.eventHistory.set(event.id, event);

      // Update correlation map
      if (event.correlationId) {
        if (!this.correlationMap.has(event.correlationId)) {
          this.correlationMap.set(event.correlationId, []);
        }
        this.correlationMap.get(event.correlationId).push(event.id);
      }

      // Publish to channels
      await this.publishToChannels(event);

      // Update statistics
      this.stats.eventsPublished++;

      // Emit published event
      this.emit('eventPublished', event);

      return event.id;

    } catch (error) {
      this.logger.error('Failed to publish event', {
        eventType,
        error: error.message,
        stack: error.stack
      });

      this.stats.eventsDropped++;
      this.emit('publishError', error, eventType, data);

      if (!options.suppressErrors) {
        throw error;
      }
    }
  }

  /**
   * Publish event to all applicable channels
   */
  async publishToChannels(event) {
    const promises = [];

    for (const [channelName, channel] of this.channels.entries()) {
      if (channel.shouldPublish(event)) {
        if (this.enableBuffering) {
          channel.addEvent(event);
        } else {
          promises.push(this.publishToChannel(channelName, channel, event));
        }
      }
    }

    if (!this.enableBuffering) {
      await Promise.allSettled(promises);
    }
  }

  /**
   * Publish to specific channel with retry logic
   */
  async publishToChannel(channelName, channel, event) {
    let attempt = 0;

    while (attempt <= event.maxRetries) {
      try {
        await channel.publish([event]);
        return;

      } catch (error) {
        attempt++;
        this.stats.channelErrors++;

        if (attempt <= event.maxRetries && this.enableRetries) {
          this.stats.retriesAttempted++;
          await this.delay(this.retryDelay * attempt);
        } else {
          this.logger.error('Channel publish failed after retries', {
            channelName,
            eventId: event.id,
            eventType: event.type,
            attempt,
            error: error.message
          });

          this.emit('channelError', channelName, event, error);
          throw error;
        }
      }
    }
  }

  /**
   * Publish flow start event
   */
  publishFlowStart(flowContext) {
    return this.publish(EVENT_TYPES.FLOW_START, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      serviceName: flowContext.serviceName,
      requestPath: flowContext.metadata?.requestPath,
      method: flowContext.tags?.method,
      userId: flowContext.userId,
      sessionId: flowContext.sessionId,
      startTime: flowContext.metrics.startTime
    }, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      priority: EVENT_PRIORITIES.NORMAL
    });
  }

  /**
   * Publish flow complete event
   */
  publishFlowComplete(flowContext) {
    return this.publish(EVENT_TYPES.FLOW_COMPLETE, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      serviceName: flowContext.serviceName,
      duration: flowContext.metrics.duration,
      serviceChain: flowContext.serviceChain,
      dependencies: Array.from(flowContext.dependencies),
      errorCount: flowContext.errors.length,
      status: flowContext.errors.length > 0 ? 'error' : 'success',
      endTime: flowContext.metrics.endTime
    }, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      priority: flowContext.errors.length > 0 ? EVENT_PRIORITIES.HIGH : EVENT_PRIORITIES.NORMAL
    });
  }

  /**
   * Publish error event
   */
  publishError(flowContext, error, operation = null) {
    return this.publish(EVENT_TYPES.ERROR_OCCURRED, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      serviceName: flowContext.serviceName,
      operation,
      error: {
        message: error.message,
        code: error.code,
        stack: error.stack
      },
      serviceChain: flowContext.serviceChain,
      timestamp: performance.now()
    }, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      priority: error.critical ? EVENT_PRIORITIES.CRITICAL : EVENT_PRIORITIES.HIGH
    });
  }

  /**
   * Publish dependency call event
   */
  publishDependencyCall(flowContext, targetService, operation = null) {
    return this.publish(EVENT_TYPES.DEPENDENCY_CALL, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      fromService: flowContext.serviceName,
      toService: targetService,
      operation,
      timestamp: performance.now()
    }, {
      flowId: flowContext.flowId,
      correlationId: flowContext.correlationId,
      priority: EVENT_PRIORITIES.NORMAL
    });
  }

  /**
   * Publish performance alert
   */
  publishPerformanceAlert(type, data, priority = EVENT_PRIORITIES.HIGH) {
    return this.publish(EVENT_TYPES.PERFORMANCE_ALERT, {
      alertType: type,
      serviceName: this.serviceName,
      ...data,
      timestamp: performance.now()
    }, {
      priority
    });
  }

  /**
   * Get events by correlation ID
   */
  getCorrelatedEvents(correlationId) {
    const eventIds = this.correlationMap.get(correlationId) || [];
    return eventIds.map(id => this.eventHistory.get(id)).filter(Boolean);
  }

  /**
   * Get channel statistics
   */
  getChannelStats() {
    const channelStats = {};

    for (const [name, channel] of this.channels.entries()) {
      channelStats[name] = {
        type: channel.type,
        enabled: channel.enabled,
        eventCount: channel.eventCount,
        errorCount: channel.errorCount,
        bufferSize: channel.buffer.length
      };
    }

    return channelStats;
  }

  /**
   * Get publisher statistics
   */
  getStats() {
    return {
      ...this.stats,
      channels: this.getChannelStats(),
      eventHistorySize: this.eventHistory.size,
      correlationMapSize: this.correlationMap.size
    };
  }

  /**
   * Flush all channel buffers
   */
  async flushAll() {
    const promises = [];

    for (const [channelName, channel] of this.channels.entries()) {
      promises.push(
        channel.flush().catch(error => {
          this.logger.error('Channel flush failed', {
            channelName,
            error: error.message
          });
        })
      );
    }

    await Promise.allSettled(promises);
  }

  /**
   * Start flush timer
   */
  startFlushTimer() {
    this.flushTimer = setInterval(async () => {
      await this.flushAll();
      this.cleanupEventHistory();
    }, this.flushInterval);
  }

  /**
   * Cleanup old events from history
   */
  cleanupEventHistory() {
    const cutoff = Date.now() - (24 * 60 * 60 * 1000); // 24 hours

    for (const [eventId, event] of this.eventHistory.entries()) {
      if (event.timestamp < cutoff) {
        this.eventHistory.delete(eventId);

        // Cleanup correlation map
        if (event.correlationId) {
          const correlatedEvents = this.correlationMap.get(event.correlationId) || [];
          const updatedEvents = correlatedEvents.filter(id => id !== eventId);

          if (updatedEvents.length === 0) {
            this.correlationMap.delete(event.correlationId);
          } else {
            this.correlationMap.set(event.correlationId, updatedEvents);
          }
        }
      }
    }
  }

  /**
   * Delay helper for retries
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Stop publisher and cleanup
   */
  async stop() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    // Final flush
    await this.flushAll();

    // Clear data
    this.channels.clear();
    this.eventHistory.clear();
    this.correlationMap.clear();
    this.removeAllListeners();
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create ChainEventPublisher instance
 */
function createChainEventPublisher(options = {}) {
  return new ChainEventPublisher(options);
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  ChainEventPublisher,
  FlowEvent,
  EventChannel,
  WebhookChannel,
  LogChannel,
  MetricsChannel,
  createChainEventPublisher,
  EVENT_TYPES,
  EVENT_PRIORITIES,
  CHANNEL_TYPES
};