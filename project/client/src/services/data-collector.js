const EventEmitter = require('events');
const WebSocket = require('ws');
const logger = require('../utils/logger');

class DataCollector extends EventEmitter {
  constructor(config, performanceMonitor) {
    super();
    this.config = config;
    this.performanceMonitor = performanceMonitor;
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 3000;
    this.dataCache = new Map();
    this.aggregationBuffer = [];
    this.isShuttingDown = false;

    // Data processing metrics
    this.metrics = {
      dataPointsProcessed: 0,
      dataPointsPerSecond: 0,
      cacheHitRate: 0,
      aggregationLatency: 0,
      lastProcessingTime: 0,
      startTime: Date.now()
    };

    // Initialize data processing intervals
    this.setupDataProcessing();
  }

  async connect() {
    try {
      logger.info('Connecting Data Collector to backend data bridge...');

      const backendUrl = this.config.backendUrl || 'ws://localhost:3001/ws';

      this.ws = new WebSocket(backendUrl, {
        headers: {
          'User-Agent': 'AI-Trading-Client/1.0.0',
          'X-Client-Type': 'data-collector',
          'X-Client-Version': '1.0.0'
        }
      });

      await this.setupWebSocketHandlers();

      // Wait for connection to be established
      await this.waitForConnection();

      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.metrics.startTime = Date.now();

      logger.info('Data Collector connected to backend successfully');
      this.emit('connected');

      // Start data collection
      this.startDataCollection();

    } catch (error) {
      logger.error('Failed to connect Data Collector:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async setupWebSocketHandlers() {
    return new Promise((resolve, reject) => {
      this.ws.on('open', () => {
        logger.info('WebSocket connection to backend established');
        resolve();
      });

      this.ws.on('message', (data) => {
        this.handleBackendMessage(data);
      });

      this.ws.on('close', (code, reason) => {
        logger.warn(`WebSocket connection closed: ${code} - ${reason}`);
        this.handleDisconnection();
      });

      this.ws.on('error', (error) => {
        logger.error('WebSocket error:', error);
        this.emit('error', error);
        if (!this.isConnected) {
          reject(error);
        }
      });

      // Connection timeout
      setTimeout(() => {
        if (!this.isConnected) {
          reject(new Error('WebSocket connection timeout'));
        }
      }, 10000);
    });
  }

  async waitForConnection() {
    return new Promise((resolve, reject) => {
      if (this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      const onOpen = () => {
        this.ws.removeListener('error', onError);
        resolve();
      };

      const onError = (error) => {
        this.ws.removeListener('open', onOpen);
        reject(error);
      };

      this.ws.once('open', onOpen);
      this.ws.once('error', onError);
    });
  }

  handleBackendMessage(data) {
    try {
      const message = JSON.parse(data.toString());

      switch (message.type) {
        case 'welcome':
          logger.info('Received welcome from backend:', message.clientId);
          this.subscribeToDataFeeds();
          break;

        case 'market_data':
          this.handleMarketDataFromBackend(message.data);
          break;

        case 'subscribed':
          logger.info(`Subscribed to ${message.symbol}:${message.dataType}`);
          break;

        case 'performance_alert':
          logger.warn('Backend performance alert:', message.alert);
          this.emit('performanceAlert', message.alert);
          break;

        case 'error':
          logger.error('Backend error:', message.message);
          this.emit('error', new Error(message.message));
          break;

        case 'pong':
          // Handle ping/pong for connection keepalive
          break;

        default:
          logger.debug('Unknown message type from backend:', message.type);
      }

    } catch (error) {
      logger.error('Error parsing backend message:', error);
    }
  }

  subscribeToDataFeeds() {
    // Subscribe to market data feeds
    const symbols = this.config.symbols || ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'];

    symbols.forEach(symbol => {
      this.sendToBackend({
        type: 'subscribe',
        symbol: symbol,
        dataType: 'tick'
      });

      this.sendToBackend({
        type: 'subscribe',
        symbol: symbol,
        dataType: 'market_data'
      });
    });

    logger.info(`Subscribed to data feeds for ${symbols.length} symbols`);
  }

  sendToBackend(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        logger.error('Error sending message to backend:', error);
      }
    }
  }

  handleMarketDataFromBackend(data) {
    // Process market data received from backend
    this.processReceivedData(data, 'backend');
  }

  setupDataProcessing() {
    // Aggregation buffer processing (every 100ms for high frequency)
    this.aggregationInterval = setInterval(() => {
      this.processAggregationBuffer();
    }, 100);

    // Cache cleanup (every 5 minutes)
    this.cacheCleanupInterval = setInterval(() => {
      this.cleanupCache();
    }, 5 * 60 * 1000);

    // Metrics calculation (every second)
    this.metricsInterval = setInterval(() => {
      this.calculateMetrics();
    }, 1000);
  }

  startDataCollection() {
    logger.info('Starting data collection and processing...');

    // Send periodic ping to maintain connection
    this.pingInterval = setInterval(() => {
      this.sendToBackend({ type: 'ping' });
    }, 30000);
  }

  processTickData(tickData) {
    const startTime = process.hrtime.bigint();

    try {
      // Enrich tick data with client information
      const enrichedTick = {
        ...tickData,
        clientProcessingTime: Date.now(),
        source: 'mt5_client',
        collectorVersion: '1.0.0'
      };

      // Add to aggregation buffer
      this.aggregationBuffer.push({
        type: 'tick',
        data: enrichedTick,
        timestamp: Date.now()
      });

      // Cache the latest tick for each symbol
      this.cacheData(`tick_${tickData.symbol}`, enrichedTick);

      // Send to backend via WebSocket
      this.sendToBackend({
        type: 'client_data',
        dataType: 'tick',
        data: enrichedTick
      });

      // Update metrics
      this.metrics.dataPointsProcessed++;

      // Record performance
      const endTime = process.hrtime.bigint();
      const processingLatency = Number(endTime - startTime) / 1000000; // Convert to ms

      this.metrics.lastProcessingTime = processingLatency;

      if (this.performanceMonitor) {
        this.performanceMonitor.recordDataProcessing({
          type: 'tick',
          symbol: tickData.symbol,
          latency: processingLatency,
          timestamp: Date.now()
        });
      }

      this.emit('dataProcessed', {
        type: 'tick',
        symbol: tickData.symbol,
        latency: processingLatency
      });

    } catch (error) {
      logger.error('Error processing tick data:', error);
      this.emit('error', error);
    }
  }

  processMarketData(marketData) {
    const startTime = process.hrtime.bigint();

    try {
      // Enrich market data
      const enrichedMarketData = {
        ...marketData,
        clientProcessingTime: Date.now(),
        source: 'mt5_client',
        collectorVersion: '1.0.0'
      };

      // Add to aggregation buffer
      this.aggregationBuffer.push({
        type: 'market_data',
        data: enrichedMarketData,
        timestamp: Date.now()
      });

      // Cache market data
      this.cacheData(`market_${marketData.symbol}`, enrichedMarketData);

      // Send to backend
      this.sendToBackend({
        type: 'client_data',
        dataType: 'market_data',
        data: enrichedMarketData
      });

      // Update metrics
      this.metrics.dataPointsProcessed++;

      const endTime = process.hrtime.bigint();
      const processingLatency = Number(endTime - startTime) / 1000000;

      this.metrics.lastProcessingTime = processingLatency;

      if (this.performanceMonitor) {
        this.performanceMonitor.recordDataProcessing({
          type: 'market_data',
          symbol: marketData.symbol,
          latency: processingLatency,
          timestamp: Date.now()
        });
      }

      this.emit('dataProcessed', {
        type: 'market_data',
        symbol: marketData.symbol,
        latency: processingLatency
      });

    } catch (error) {
      logger.error('Error processing market data:', error);
      this.emit('error', error);
    }
  }

  processReceivedData(data, source) {
    // Process data received from backend
    try {
      const processedData = {
        ...data,
        receivedAt: Date.now(),
        source: source
      };

      // Cache received data
      if (data.symbol) {
        this.cacheData(`received_${data.symbol}`, processedData);
      }

      this.emit('dataReceived', processedData);

    } catch (error) {
      logger.error('Error processing received data:', error);
    }
  }

  processAggregationBuffer() {
    if (this.aggregationBuffer.length === 0) return;

    const startTime = process.hrtime.bigint();

    try {
      const bufferCopy = [...this.aggregationBuffer];
      this.aggregationBuffer = [];

      // Group data by symbol and type
      const groupedData = this.groupDataForAggregation(bufferCopy);

      // Calculate aggregated metrics
      const aggregatedData = this.calculateAggregatedMetrics(groupedData);

      // Send aggregated data to backend
      if (Object.keys(aggregatedData).length > 0) {
        this.sendToBackend({
          type: 'aggregated_data',
          data: aggregatedData,
          timestamp: Date.now(),
          bufferSize: bufferCopy.length
        });
      }

      const endTime = process.hrtime.bigint();
      this.metrics.aggregationLatency = Number(endTime - startTime) / 1000000;

    } catch (error) {
      logger.error('Error processing aggregation buffer:', error);
    }
  }

  groupDataForAggregation(buffer) {
    const grouped = {};

    buffer.forEach(item => {
      const key = `${item.data.symbol}_${item.type}`;

      if (!grouped[key]) {
        grouped[key] = {
          symbol: item.data.symbol,
          type: item.type,
          items: []
        };
      }

      grouped[key].items.push(item);
    });

    return grouped;
  }

  calculateAggregatedMetrics(groupedData) {
    const aggregated = {};

    Object.keys(groupedData).forEach(key => {
      const group = groupedData[key];
      const items = group.items;

      if (items.length === 0) return;

      if (group.type === 'tick') {
        // Calculate tick aggregations
        const bids = items.map(item => item.data.bid).filter(bid => bid != null);
        const asks = items.map(item => item.data.ask).filter(ask => ask != null);
        const volumes = items.map(item => item.data.volume).filter(vol => vol != null);

        aggregated[key] = {
          symbol: group.symbol,
          type: 'tick_aggregated',
          count: items.length,
          bid: {
            min: Math.min(...bids),
            max: Math.max(...bids),
            avg: bids.reduce((a, b) => a + b, 0) / bids.length,
            last: bids[bids.length - 1]
          },
          ask: {
            min: Math.min(...asks),
            max: Math.max(...asks),
            avg: asks.reduce((a, b) => a + b, 0) / asks.length,
            last: asks[asks.length - 1]
          },
          volume: {
            total: volumes.reduce((a, b) => a + b, 0),
            avg: volumes.length > 0 ? volumes.reduce((a, b) => a + b, 0) / volumes.length : 0,
            max: volumes.length > 0 ? Math.max(...volumes) : 0
          },
          timeRange: {
            start: Math.min(...items.map(item => item.timestamp)),
            end: Math.max(...items.map(item => item.timestamp))
          }
        };
      }
    });

    return aggregated;
  }

  cacheData(key, data) {
    const cacheEntry = {
      data: data,
      timestamp: Date.now(),
      accessCount: 0
    };

    this.dataCache.set(key, cacheEntry);

    // Limit cache size
    if (this.dataCache.size > 10000) {
      this.cleanupCache();
    }
  }

  getCachedData(key) {
    const entry = this.dataCache.get(key);
    if (entry) {
      entry.accessCount++;
      return entry.data;
    }
    return null;
  }

  cleanupCache() {
    const now = Date.now();
    const maxAge = 5 * 60 * 1000; // 5 minutes
    let removed = 0;

    this.dataCache.forEach((entry, key) => {
      if (now - entry.timestamp > maxAge || entry.accessCount === 0) {
        this.dataCache.delete(key);
        removed++;
      }
    });

    if (removed > 0) {
      logger.debug(`Cleaned up ${removed} cache entries`);
    }
  }

  calculateMetrics() {
    const now = Date.now();
    const uptime = now - this.metrics.startTime;

    if (uptime > 0) {
      this.metrics.dataPointsPerSecond = (this.metrics.dataPointsProcessed / uptime) * 1000;
    }

    // Calculate cache hit rate (simplified)
    const totalCacheAccess = Array.from(this.dataCache.values())
      .reduce((total, entry) => total + entry.accessCount, 0);

    this.metrics.cacheHitRate = this.dataCache.size > 0 ?
      (totalCacheAccess / this.dataCache.size) * 100 : 0;
  }

  async reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      throw new Error('Maximum reconnection attempts reached');
    }

    this.reconnectAttempts++;
    logger.info(`Reconnecting Data Collector (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    try {
      await this.disconnect();

      // Wait before reconnecting with exponential backoff
      const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
      await new Promise(resolve => setTimeout(resolve, delay));

      await this.connect();

    } catch (error) {
      logger.error('Data Collector reconnection failed:', error);
      throw error;
    }
  }

  async disconnect() {
    logger.info('Disconnecting Data Collector...');

    this.isConnected = false;
    this.isShuttingDown = true;

    try {
      // Clear intervals
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }

      if (this.aggregationInterval) {
        clearInterval(this.aggregationInterval);
        this.aggregationInterval = null;
      }

      if (this.cacheCleanupInterval) {
        clearInterval(this.cacheCleanupInterval);
        this.cacheCleanupInterval = null;
      }

      if (this.metricsInterval) {
        clearInterval(this.metricsInterval);
        this.metricsInterval = null;
      }

      // Close WebSocket connection
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }

      // Clear cache
      this.dataCache.clear();
      this.aggregationBuffer = [];

      logger.info('Data Collector disconnected successfully');
      this.emit('disconnected');

    } catch (error) {
      logger.error('Error during Data Collector disconnection:', error);
    }
  }

  handleDisconnection() {
    this.isConnected = false;
    this.emit('disconnected');

    // Attempt automatic reconnection
    if (!this.isShuttingDown && this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnect().catch(error => {
          logger.error('Auto-reconnection failed:', error);
        });
      }, this.reconnectDelay);
    }
  }

  // Public interface methods
  isConnected() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  getMetrics() {
    return {
      ...this.metrics,
      cacheSize: this.dataCache.size,
      bufferSize: this.aggregationBuffer.length,
      uptime: Date.now() - this.metrics.startTime,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      websocketState: this.ws ? this.ws.readyState : -1,
      reconnectAttempts: this.reconnectAttempts,
      lastError: this.lastError
    };
  }

  getCacheStatus() {
    return {
      size: this.dataCache.size,
      hitRate: this.metrics.cacheHitRate,
      entries: Array.from(this.dataCache.keys()).slice(0, 10) // Sample of cache keys
    };
  }
}

module.exports = DataCollector;