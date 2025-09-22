/**
 * Level 3 Real-time Streaming Service
 * Event-driven real-time data distribution for Level 3 requirements
 */

const EventEmitter = require('events');
const WebSocket = require('ws');
const logger = require('../utils/logger');

class RealTimeStreamingService extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      maxConnections: 1000,
      heartbeatInterval: 30000, // 30 seconds
      compressionEnabled: true,
      rateLimitPerSecond: 100,
      bufferSize: 1000,
      enableMetrics: true,
      ...config
    };

    this.connections = new Map(); // connectionId -> connection info
    this.subscriptions = new Map(); // symbol -> Set of connectionIds
    this.messageBuffer = new Map(); // connectionId -> message buffer
    this.rateLimits = new Map(); // connectionId -> rate limit info

    this.metrics = {
      totalConnections: 0,
      activeConnections: 0,
      messagesDelivered: 0,
      messagesSent: 0,
      bytesTransferred: 0,
      averageLatency: 0,
      lastUpdate: Date.now()
    };

    this.setupMetricsCollection();
  }

  /**
   * Level 3: Initialize streaming service with WebSocket server
   * @param {WebSocket.Server} wss - WebSocket server instance
   */
  initialize(wss) {
    this.wss = wss;
    this.setupWebSocketHandlers();
    this.startHeartbeat();

    logger.info('Real-time streaming service initialized');
    this.emit('serviceInitialized', {
      maxConnections: this.config.maxConnections,
      features: ['real-time-streaming', 'compression', 'rate-limiting', 'metrics']
    });
  }

  setupWebSocketHandlers() {
    if (!this.wss) {
      throw new Error('WebSocket server not provided');
    }

    this.wss.on('connection', (ws, req) => {
      this.handleNewConnection(ws, req);
    });
  }

  handleNewConnection(ws, req) {
    const connectionId = this.generateConnectionId();
    const clientIP = req.socket.remoteAddress;

    // Check connection limits
    if (this.connections.size >= this.config.maxConnections) {
      logger.warn(`Connection limit reached, rejecting connection from ${clientIP}`);
      ws.close(1013, 'Service overloaded');
      return;
    }

    // Initialize connection
    const connection = {
      id: connectionId,
      ws: ws,
      ip: clientIP,
      connectedAt: new Date().toISOString(),
      lastActivity: Date.now(),
      subscriptions: new Set(),
      messageCount: 0,
      bytesReceived: 0,
      bytesSent: 0,
      authenticated: false,
      metadata: {
        userAgent: req.headers['user-agent'],
        origin: req.headers.origin
      }
    };

    this.connections.set(connectionId, connection);
    this.messageBuffer.set(connectionId, []);
    this.rateLimits.set(connectionId, {
      tokens: this.config.rateLimitPerSecond,
      lastRefill: Date.now()
    });

    this.metrics.totalConnections++;
    this.metrics.activeConnections++;

    logger.info(`New streaming connection: ${connectionId} from ${clientIP}`);

    // Setup connection event handlers
    ws.on('message', (data) => {
      this.handleMessage(connectionId, data);
    });

    ws.on('close', (code, reason) => {
      this.handleDisconnection(connectionId, code, reason);
    });

    ws.on('error', (error) => {
      this.handleConnectionError(connectionId, error);
    });

    // Send welcome message
    this.sendToConnection(connectionId, {
      type: 'welcome',
      connectionId: connectionId,
      timestamp: new Date().toISOString(),
      features: ['real-time-data', 'symbol-subscription', 'multi-source-aggregation'],
      limits: {
        maxSubscriptions: 50,
        rateLimit: this.config.rateLimitPerSecond
      }
    });

    this.emit('connectionEstablished', { connectionId, connection });
  }

  handleMessage(connectionId, data) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    try {
      connection.lastActivity = Date.now();
      connection.bytesReceived += data.length;

      // Rate limiting check
      if (!this.checkRateLimit(connectionId)) {
        this.sendToConnection(connectionId, {
          type: 'error',
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Rate limit exceeded. Please slow down.'
        });
        return;
      }

      const message = JSON.parse(data.toString());
      connection.messageCount++;

      logger.debug(`Message from ${connectionId}:`, message);

      // Handle different message types
      switch (message.type) {
        case 'subscribe':
          this.handleSubscription(connectionId, message);
          break;
        case 'unsubscribe':
          this.handleUnsubscription(connectionId, message);
          break;
        case 'ping':
          this.handlePing(connectionId);
          break;
        case 'authenticate':
          this.handleAuthentication(connectionId, message);
          break;
        case 'get_status':
          this.handleStatusRequest(connectionId);
          break;
        default:
          this.sendToConnection(connectionId, {
            type: 'error',
            code: 'UNKNOWN_MESSAGE_TYPE',
            message: `Unknown message type: ${message.type}`
          });
      }

    } catch (error) {
      logger.error(`Error processing message from ${connectionId}:`, error);
      this.sendToConnection(connectionId, {
        type: 'error',
        code: 'MESSAGE_PARSE_ERROR',
        message: 'Invalid message format'
      });
    }
  }

  handleSubscription(connectionId, message) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    const { symbol, dataType = 'tick' } = message;

    if (!symbol) {
      this.sendToConnection(connectionId, {
        type: 'error',
        code: 'MISSING_SYMBOL',
        message: 'Symbol is required for subscription'
      });
      return;
    }

    // Check subscription limits
    if (connection.subscriptions.size >= 50) {
      this.sendToConnection(connectionId, {
        type: 'error',
        code: 'SUBSCRIPTION_LIMIT_EXCEEDED',
        message: 'Maximum number of subscriptions reached'
      });
      return;
    }

    const subscriptionKey = `${symbol}:${dataType}`;

    // Add to connection subscriptions
    connection.subscriptions.add(subscriptionKey);

    // Add to global subscriptions
    if (!this.subscriptions.has(subscriptionKey)) {
      this.subscriptions.set(subscriptionKey, new Set());
    }
    this.subscriptions.get(subscriptionKey).add(connectionId);

    this.sendToConnection(connectionId, {
      type: 'subscription_confirmed',
      symbol,
      dataType,
      timestamp: new Date().toISOString()
    });

    logger.info(`Connection ${connectionId} subscribed to ${subscriptionKey}`);
    this.emit('symbolSubscribed', { connectionId, symbol, dataType });
  }

  handleUnsubscription(connectionId, message) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    const { symbol, dataType = 'tick' } = message;
    const subscriptionKey = `${symbol}:${dataType}`;

    // Remove from connection subscriptions
    connection.subscriptions.delete(subscriptionKey);

    // Remove from global subscriptions
    if (this.subscriptions.has(subscriptionKey)) {
      this.subscriptions.get(subscriptionKey).delete(connectionId);

      // Clean up empty subscription sets
      if (this.subscriptions.get(subscriptionKey).size === 0) {
        this.subscriptions.delete(subscriptionKey);
      }
    }

    this.sendToConnection(connectionId, {
      type: 'unsubscription_confirmed',
      symbol,
      dataType,
      timestamp: new Date().toISOString()
    });

    logger.info(`Connection ${connectionId} unsubscribed from ${subscriptionKey}`);
    this.emit('symbolUnsubscribed', { connectionId, symbol, dataType });
  }

  handlePing(connectionId) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    connection.lastActivity = Date.now();

    this.sendToConnection(connectionId, {
      type: 'pong',
      timestamp: new Date().toISOString(),
      serverTime: Date.now()
    });
  }

  handleAuthentication(connectionId, message) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Simplified authentication (in production, use proper JWT validation)
    const { token } = message;

    if (token && token.startsWith('Bearer ')) {
      connection.authenticated = true;
      this.sendToConnection(connectionId, {
        type: 'authentication_success',
        timestamp: new Date().toISOString()
      });
      logger.info(`Connection ${connectionId} authenticated successfully`);
    } else {
      this.sendToConnection(connectionId, {
        type: 'authentication_failed',
        message: 'Invalid authentication token'
      });
    }
  }

  handleStatusRequest(connectionId) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    this.sendToConnection(connectionId, {
      type: 'status_response',
      connectionStatus: {
        id: connectionId,
        connectedAt: connection.connectedAt,
        authenticated: connection.authenticated,
        subscriptions: Array.from(connection.subscriptions),
        messageCount: connection.messageCount,
        bytesTransferred: {
          received: connection.bytesReceived,
          sent: connection.bytesSent
        }
      },
      serverStatus: this.getServerStatus(),
      timestamp: new Date().toISOString()
    });
  }

  handleDisconnection(connectionId, code, reason) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Clean up subscriptions
    connection.subscriptions.forEach(subscriptionKey => {
      if (this.subscriptions.has(subscriptionKey)) {
        this.subscriptions.get(subscriptionKey).delete(connectionId);

        // Clean up empty subscription sets
        if (this.subscriptions.get(subscriptionKey).size === 0) {
          this.subscriptions.delete(subscriptionKey);
        }
      }
    });

    // Clean up connection data
    this.connections.delete(connectionId);
    this.messageBuffer.delete(connectionId);
    this.rateLimits.delete(connectionId);

    this.metrics.activeConnections--;

    logger.info(`Connection ${connectionId} disconnected (code: ${code}, reason: ${reason})`);
    this.emit('connectionClosed', { connectionId, code, reason });
  }

  handleConnectionError(connectionId, error) {
    logger.error(`Connection error for ${connectionId}:`, error);
    this.handleDisconnection(connectionId, 1011, 'Internal server error');
  }

  /**
   * Level 3: Stream market data to subscribed connections
   * @param {Object} tickData - Market tick data
   */
  streamTickData(tickData) {
    const { symbol, dataType = 'tick' } = tickData;
    const subscriptionKey = `${symbol}:${dataType}`;

    if (!this.subscriptions.has(subscriptionKey)) {
      return; // No subscribers for this symbol
    }

    const subscribers = this.subscriptions.get(subscriptionKey);
    const message = {
      type: 'market_data',
      data: tickData,
      timestamp: new Date().toISOString(),
      source: 'real-time-stream'
    };

    let deliveredCount = 0;

    subscribers.forEach(connectionId => {
      if (this.sendToConnection(connectionId, message)) {
        deliveredCount++;
      }
    });

    // Update metrics
    this.metrics.messagesDelivered += deliveredCount;
    this.metrics.messagesSent++;

    this.emit('dataStreamed', {
      symbol,
      dataType,
      subscriberCount: subscribers.size,
      deliveredCount,
      data: tickData
    });
  }

  /**
   * Level 3: Broadcast message to all connections
   * @param {Object} message - Message to broadcast
   * @param {Function} filter - Optional filter function
   */
  broadcast(message, filter = null) {
    let deliveredCount = 0;

    this.connections.forEach((connection, connectionId) => {
      if (filter && !filter(connection)) return;

      if (this.sendToConnection(connectionId, message)) {
        deliveredCount++;
      }
    });

    return deliveredCount;
  }

  sendToConnection(connectionId, message) {
    const connection = this.connections.get(connectionId);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      const messageString = JSON.stringify(message);
      const messageSize = Buffer.byteLength(messageString, 'utf8');

      connection.ws.send(messageString);
      connection.bytesSent += messageSize;
      this.metrics.bytesTransferred += messageSize;

      return true;
    } catch (error) {
      logger.error(`Error sending message to ${connectionId}:`, error);
      this.handleConnectionError(connectionId, error);
      return false;
    }
  }

  checkRateLimit(connectionId) {
    const rateLimitInfo = this.rateLimits.get(connectionId);
    if (!rateLimitInfo) return false;

    const now = Date.now();
    const timeDiff = now - rateLimitInfo.lastRefill;

    // Refill tokens based on time elapsed
    if (timeDiff >= 1000) { // 1 second
      rateLimitInfo.tokens = this.config.rateLimitPerSecond;
      rateLimitInfo.lastRefill = now;
    }

    if (rateLimitInfo.tokens > 0) {
      rateLimitInfo.tokens--;
      return true;
    }

    return false;
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.performHeartbeat();
    }, this.config.heartbeatInterval);
  }

  performHeartbeat() {
    const now = Date.now();
    const deadConnections = [];

    this.connections.forEach((connection, connectionId) => {
      // Check for inactive connections (no activity for 2 minutes)
      if (now - connection.lastActivity > 120000) {
        deadConnections.push(connectionId);
        return;
      }

      // Send heartbeat ping
      this.sendToConnection(connectionId, {
        type: 'heartbeat',
        timestamp: new Date().toISOString()
      });
    });

    // Clean up dead connections
    deadConnections.forEach(connectionId => {
      logger.warn(`Removing inactive connection: ${connectionId}`);
      const connection = this.connections.get(connectionId);
      if (connection && connection.ws.readyState === WebSocket.OPEN) {
        connection.ws.close(1000, 'Heartbeat timeout');
      }
      this.handleDisconnection(connectionId, 1000, 'Heartbeat timeout');
    });
  }

  setupMetricsCollection() {
    if (!this.config.enableMetrics) return;

    // Collect metrics every 5 seconds
    this.metricsInterval = setInterval(() => {
      this.updateMetrics();
    }, 5000);
  }

  updateMetrics() {
    const now = Date.now();
    const timeDiff = now - this.metrics.lastUpdate;

    // Calculate throughput rates
    this.metrics.messageRate = (this.metrics.messagesSent * 1000) / timeDiff;
    this.metrics.dataRate = (this.metrics.bytesTransferred * 1000) / timeDiff;

    this.metrics.lastUpdate = now;

    this.emit('metricsUpdated', this.getMetrics());
  }

  getMetrics() {
    return {
      ...this.metrics,
      connections: {
        total: this.metrics.totalConnections,
        active: this.metrics.activeConnections,
        subscriptions: this.subscriptions.size
      },
      performance: {
        averageLatency: this.metrics.averageLatency,
        messageRate: this.metrics.messageRate || 0,
        dataRate: this.metrics.dataRate || 0
      },
      timestamp: new Date().toISOString()
    };
  }

  getServerStatus() {
    return {
      activeConnections: this.metrics.activeConnections,
      totalSubscriptions: this.subscriptions.size,
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      performance: this.getMetrics().performance
    };
  }

  generateConnectionId() {
    return `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Cleanup method
  shutdown() {
    logger.info('Shutting down real-time streaming service...');

    // Clear intervals
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }

    // Close all connections
    this.connections.forEach((connection, connectionId) => {
      if (connection.ws.readyState === WebSocket.OPEN) {
        connection.ws.close(1001, 'Server shutdown');
      }
    });

    // Clear data structures
    this.connections.clear();
    this.subscriptions.clear();
    this.messageBuffer.clear();
    this.rateLimits.clear();

    this.emit('serviceShutdown');
  }
}

module.exports = RealTimeStreamingService;