const EventEmitter = require('events');
const axios = require('axios');
const WebSocket = require('ws');
const logger = require('../utils/logger');

class MT5Integration extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.dataBridgeUrl = options.dataBridgeUrl || process.env.DATA_BRIDGE_URL || 'http://localhost:3002';
    this.wsUrl = options.wsUrl || process.env.DATA_BRIDGE_WS || 'ws://localhost:3002/ws';
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.reconnectInterval = options.reconnectInterval || 5000;
    
    this.ws = null;
    this.subscriptions = new Map();
    this.priceCache = new Map();
    this.lastHeartbeat = null;
    
    this.performanceMetrics = {
      messagesReceived: 0,
      messagesProcessed: 0,
      averageLatency: 0,
      lastLatency: 0,
      connectionUptime: 0,
      errors: 0
    };
  }

  /**
   * Connect to MT5 data bridge
   */
  async connect() {
    try {
      logger.info('Connecting to MT5 data bridge', {
        dataBridgeUrl: this.dataBridgeUrl,
        wsUrl: this.wsUrl
      });
      
      // Test HTTP connection first
      await this.testHttpConnection();
      
      // Establish WebSocket connection
      await this.connectWebSocket();
      
      this.connected = true;
      this.reconnectAttempts = 0;
      this.performanceMetrics.connectionUptime = Date.now();
      
      logger.info('MT5 integration connected successfully');
      this.emit('connected');
      
    } catch (error) {
      logger.error('Failed to connect to MT5 data bridge', { error: error.message });
      this.handleConnectionError(error);
      throw error;
    }
  }

  /**
   * Test HTTP connection to data bridge
   */
  async testHttpConnection() {
    const response = await axios.get(`${this.dataBridgeUrl}/health`, {
      timeout: 5000
    });
    
    if (response.status !== 200) {
      throw new Error(`Data bridge health check failed: ${response.status}`);
    }
    
    logger.info('MT5 data bridge health check passed', {
      status: response.data.status,
      mt5Connected: response.data.mt5Connected
    });
    
    return response.data;
  }

  /**
   * Connect WebSocket for real-time data
   */
  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      
      this.ws.on('open', () => {
        logger.info('WebSocket connection established');
        this.setupHeartbeat();
        resolve();
      });
      
      this.ws.on('message', (data) => {
        this.handleWebSocketMessage(data);
      });
      
      this.ws.on('close', () => {
        logger.warn('WebSocket connection closed');
        this.connected = false;
        this.attemptReconnect();
      });
      
      this.ws.on('error', (error) => {
        logger.error('WebSocket error', { error: error.message });
        reject(error);
      });
      
      // Connection timeout
      setTimeout(() => {
        if (this.ws.readyState !== WebSocket.OPEN) {
          reject(new Error('WebSocket connection timeout'));
        }
      }, 10000);
    });
  }

  /**
   * Handle WebSocket messages
   */
  handleWebSocketMessage(data) {
    const startTime = Date.now();
    
    try {
      const message = JSON.parse(data.toString());
      this.performanceMetrics.messagesReceived++;
      
      switch (message.type) {
        case 'market_data':
          this.handleMarketData(message.data);
          break;
        case 'pong':
          this.handlePong(message);
          break;
        case 'error':
          this.handleError(message);
          break;
        case 'welcome':
          this.handleWelcome(message);
          break;
        default:
          logger.debug('Unknown message type', { type: message.type });
      }
      
      this.performanceMetrics.messagesProcessed++;
      
    } catch (error) {
      logger.error('Error parsing WebSocket message', { error: error.message });
      this.performanceMetrics.errors++;
    }
    
    const latency = Date.now() - startTime;
    this.updateLatencyMetrics(latency);
  }

  /**
   * Handle market data updates
   */
  handleMarketData(data) {
    const { symbol, bid, ask, timestamp, volume } = data;
    
    if (!symbol || !bid || !ask) {
      logger.warn('Invalid market data received', { data });
      return;
    }
    
    // Update price cache
    this.priceCache.set(symbol, {
      bid,
      ask,
      spread: ask - bid,
      timestamp,
      volume,
      lastUpdate: Date.now()
    });
    
    // Emit for correlation analyzer and other services
    this.emit('priceUpdate', {
      symbol,
      price: (bid + ask) / 2, // Mid price
      bid,
      ask,
      timestamp
    });
    
    logger.market.data(symbol, bid, ask, ask - bid, Date.now() - timestamp);
  }

  /**
   * Subscribe to symbol data
   */
  async subscribeToSymbol(symbol, dataType = 'tick') {
    if (!this.connected) {
      throw new Error('Not connected to MT5 data bridge');
    }
    
    if (this.subscriptions.has(symbol)) {
      logger.warn('Already subscribed to symbol', { symbol });
      return;
    }
    
    try {
      const message = {
        type: 'subscribe',
        symbol,
        dataType
      };
      
      this.ws.send(JSON.stringify(message));
      
      this.subscriptions.set(symbol, {
        symbol,
        dataType,
        subscribedAt: Date.now()
      });
      
      logger.info('Subscribed to symbol', { symbol, dataType });
      
    } catch (error) {
      logger.error('Failed to subscribe to symbol', { symbol, error: error.message });
      throw error;
    }
  }

  /**
   * Unsubscribe from symbol data
   */
  async unsubscribeFromSymbol(symbol) {
    if (!this.subscriptions.has(symbol)) {
      logger.warn('Not subscribed to symbol', { symbol });
      return;
    }
    
    try {
      const message = {
        type: 'unsubscribe',
        symbol
      };
      
      this.ws.send(JSON.stringify(message));
      this.subscriptions.delete(symbol);
      
      logger.info('Unsubscribed from symbol', { symbol });
      
    } catch (error) {
      logger.error('Failed to unsubscribe from symbol', { symbol, error: error.message });
      throw error;
    }
  }

  /**
   * Get current market data for symbol
   */
  async getMarketData(symbol) {
    // Try cache first
    const cached = this.priceCache.get(symbol);
    if (cached && (Date.now() - cached.lastUpdate) < 5000) { // 5 second cache
      return cached;
    }
    
    // Fetch from HTTP API if not cached or stale
    try {
      const response = await axios.get(`${this.dataBridgeUrl}/api/market-data/${symbol}`, {
        timeout: 2000
      });
      
      if (response.data && response.data.length > 0) {
        const latest = response.data[response.data.length - 1];
        const marketData = {
          bid: latest.close - 0.0001, // Mock bid
          ask: latest.close + 0.0001, // Mock ask
          spread: 0.0002,
          timestamp: new Date(latest.timestamp).getTime(),
          volume: latest.volume,
          lastUpdate: Date.now()
        };
        
        this.priceCache.set(symbol, marketData);
        return marketData;
      }
      
      throw new Error('No market data available');
      
    } catch (error) {
      logger.error('Failed to fetch market data', { symbol, error: error.message });
      throw error;
    }
  }

  /**
   * Get available symbols
   */
  async getAvailableSymbols() {
    try {
      const response = await axios.get(`${this.dataBridgeUrl}/api/symbols`, {
        timeout: 5000
      });
      
      return response.data || [];
      
    } catch (error) {
      logger.error('Failed to fetch symbols', { error: error.message });
      throw error;
    }
  }

  /**
   * Execute order through MT5
   */
  async executeOrder(order) {
    try {
      // This would integrate with the actual MT5 execution system
      // For now, we'll simulate the execution
      const marketData = await this.getMarketData(order.symbol);
      
      const executionPrice = order.side === 'buy' ? marketData.ask : marketData.bid;
      
      const execution = {
        id: `MT5_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        orderId: order.id,
        symbol: order.symbol,
        side: order.side,
        quantity: order.quantity,
        price: executionPrice,
        commission: this.calculateCommission(order, executionPrice),
        timestamp: Date.now(),
        source: 'mt5_bridge'
      };
      
      logger.order.executed(order.id, execution, 0);
      
      return execution;
      
    } catch (error) {
      logger.error('Order execution failed', { order, error: error.message });
      throw error;
    }
  }

  /**
   * Calculate commission
   */
  calculateCommission(order, price) {
    const notionalValue = order.quantity * price;
    const commissionRate = 0.0002; // 0.02%
    return notionalValue * commissionRate;
  }

  /**
   * Setup heartbeat to monitor connection
   */
  setupHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, 30000); // 30 seconds
  }

  /**
   * Handle pong response
   */
  handlePong(message) {
    this.lastHeartbeat = Date.now();
    const latency = this.lastHeartbeat - message.timestamp;
    logger.debug('Heartbeat latency', { latency });
  }

  /**
   * Handle welcome message
   */
  handleWelcome(message) {
    logger.info('Received welcome from data bridge', { clientId: message.clientId });
  }

  /**
   * Handle error messages
   */
  handleError(message) {
    logger.error('Error from data bridge', { error: message.message });
    this.performanceMetrics.errors++;
  }

  /**
   * Handle connection errors and attempt reconnection
   */
  handleConnectionError(error) {
    this.connected = false;
    this.performanceMetrics.errors++;
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    } else {
      logger.error('Max reconnection attempts reached', {
        attempts: this.reconnectAttempts,
        maxAttempts: this.maxReconnectAttempts
      });
      this.emit('maxReconnectAttemptsReached');
    }
  }

  /**
   * Attempt to reconnect
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    
    this.reconnectAttempts++;
    
    logger.info('Attempting to reconnect', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts
    });
    
    setTimeout(async () => {
      try {
        await this.connect();
        
        // Re-subscribe to previous subscriptions
        for (const [symbol, subscription] of this.subscriptions.entries()) {
          await this.subscribeToSymbol(symbol, subscription.dataType);
        }
        
      } catch (error) {
        logger.error('Reconnection attempt failed', { error: error.message });
        this.handleConnectionError(error);
      }
    }, this.reconnectInterval);
  }

  /**
   * Update latency metrics
   */
  updateLatencyMetrics(latency) {
    this.performanceMetrics.lastLatency = latency;
    
    // Calculate rolling average
    if (this.performanceMetrics.averageLatency === 0) {
      this.performanceMetrics.averageLatency = latency;
    } else {
      this.performanceMetrics.averageLatency = 
        (this.performanceMetrics.averageLatency * 0.9) + (latency * 0.1);
    }
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    return {
      ...this.performanceMetrics,
      connected: this.connected,
      subscriptions: this.subscriptions.size,
      cachedPairs: this.priceCache.size,
      reconnectAttempts: this.reconnectAttempts,
      uptime: this.connected ? Date.now() - this.performanceMetrics.connectionUptime : 0
    };
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      connected: this.connected,
      wsState: this.ws ? this.ws.readyState : null,
      lastHeartbeat: this.lastHeartbeat,
      subscriptions: Array.from(this.subscriptions.keys()),
      reconnectAttempts: this.reconnectAttempts,
      dataBridgeUrl: this.dataBridgeUrl
    };
  }

  /**
   * Disconnect from MT5 data bridge
   */
  async disconnect() {
    logger.info('Disconnecting from MT5 data bridge');
    
    this.connected = false;
    
    // Clear heartbeat
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    // Clear subscriptions and cache
    this.subscriptions.clear();
    this.priceCache.clear();
    
    this.emit('disconnected');
    logger.info('MT5 integration disconnected');
  }
}

module.exports = MT5Integration;