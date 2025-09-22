const EventEmitter = require('events');
const { spawn } = require('child_process');
const path = require('path');
const logger = require('../utils/logger');

class MetaTraderConnector extends EventEmitter {
  constructor(config, securityManager) {
    super();
    this.config = config;
    this.securityManager = securityManager;
    this.connections = new Map(); // Connection pool
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 5000;
    this.pythonProcess = null;
    this.performanceMetrics = {
      ticksProcessed: 0,
      lastTickTime: 0,
      averageLatency: 0,
      connectionUptime: 0,
      startTime: Date.now()
    };
  }

  async connect() {
    try {
      logger.info('Connecting to MetaTrader 5...');

      // Get encrypted credentials
      const credentials = await this.securityManager.getCredentials('mt5');

      if (!credentials) {
        throw new Error('MT5 credentials not found. Please configure credentials first.');
      }

      // Initialize connection pool (5 connections as specified)
      await this.initializeConnectionPool(credentials);

      // Start Python MT5 bridge
      await this.startMT5Bridge(credentials);

      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.performanceMetrics.startTime = Date.now();

      logger.info('MetaTrader 5 connected successfully');
      this.emit('connected');

      // Start data streaming
      this.startDataStreaming();

    } catch (error) {
      logger.error('Failed to connect to MT5:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async initializeConnectionPool(credentials) {
    logger.info('Initializing MT5 connection pool...');

    const maxConnections = Math.min(this.config.maxConnections || 5, 5); // Limit to max 5 connections

    for (let i = 0; i < maxConnections; i++) {
      const connectionId = `mt5_conn_${i}`;

      try {
        const connection = await this.createConnection(connectionId, credentials);
        this.connections.set(connectionId, {
          id: connectionId,
          connection,
          active: true,
          lastUsed: Date.now(),
          metrics: {
            requests: 0,
            errors: 0,
            avgResponseTime: 0
          }
        });

        logger.info(`MT5 connection ${connectionId} established`);

      } catch (error) {
        logger.error(`Failed to create connection ${connectionId}:`, error);
      }
    }

    logger.info(`Connection pool initialized with ${this.connections.size} connections`);
  }

  async createConnection(connectionId, credentials) {
    // This would be replaced with actual MT5 connection logic
    // For now, we're simulating the connection
    return {
      id: connectionId,
      server: credentials.server,
      login: credentials.login,
      connected: true,
      lastActivity: Date.now()
    };
  }

  async startMT5Bridge(credentials) {
    logger.info('Starting Python MT5 bridge...');

    const pythonScript = path.join(__dirname, '../python/mt5_bridge.py');

    this.pythonProcess = spawn('python', [
      pythonScript,
      '--server', credentials.server,
      '--login', credentials.login,
      '--password', credentials.password,
      '--max-connections', (this.config.maxConnections || 5).toString(),
      '--target-tps', (this.config.targetTicksPerSecond || 50).toString()
    ]);

    this.pythonProcess.stdout.on('data', (data) => {
      this.handlePythonOutput(data.toString());
    });

    this.pythonProcess.stderr.on('data', (data) => {
      logger.error('Python bridge error:', data.toString());
    });

    this.pythonProcess.on('close', (code) => {
      logger.warn(`Python bridge exited with code ${code}`);
      if (!this.isShuttingDown) {
        this.handleDisconnection();
      }
    });

    this.pythonProcess.on('error', (error) => {
      logger.error('Python bridge process error:', error);
      this.emit('error', error);
    });

    // Wait for bridge to initialize
    await this.waitForBridgeReady();
  }

  async waitForBridgeReady(timeout = 30000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('MT5 bridge initialization timeout'));
      }, timeout);

      const onReady = () => {
        clearTimeout(timer);
        resolve();
      };

      this.once('bridgeReady', onReady);
    });
  }

  handlePythonOutput(output) {
    try {
      const lines = output.trim().split('\n');

      for (const line of lines) {
        if (line.startsWith('READY:')) {
          this.emit('bridgeReady');
          continue;
        }

        if (line.startsWith('TICK:')) {
          const tickData = JSON.parse(line.substring(5));
          this.handleTickData(tickData);
          continue;
        }

        if (line.startsWith('MARKET:')) {
          const marketData = JSON.parse(line.substring(7));
          this.handleMarketData(marketData);
          continue;
        }

        if (line.startsWith('ERROR:')) {
          const error = line.substring(6);
          logger.error('MT5 bridge error:', error);
          this.emit('error', new Error(error));
          continue;
        }

        if (line.startsWith('METRICS:')) {
          const metrics = JSON.parse(line.substring(8));
          this.updatePerformanceMetrics(metrics);
          continue;
        }

        // Log other output
        if (line.trim()) {
          logger.debug('MT5 bridge:', line);
        }
      }

    } catch (error) {
      logger.error('Error parsing Python output:', error);
    }
  }

  handleTickData(tickData) {
    const now = Date.now();

    // Update performance metrics
    this.performanceMetrics.ticksProcessed++;
    this.performanceMetrics.lastTickTime = now;

    // Calculate latency (if timestamp provided)
    if (tickData.timestamp) {
      const latency = now - tickData.timestamp;
      this.updateLatencyMetrics(latency);
    }

    // Add client-side enrichment
    const enrichedTick = {
      ...tickData,
      clientTimestamp: now,
      connectionId: this.getOptimalConnection(),
      processingLatency: Date.now() - (tickData.timestamp || now)
    };

    this.emit('tick', enrichedTick);
  }

  handleMarketData(marketData) {
    const enrichedMarketData = {
      ...marketData,
      clientTimestamp: Date.now(),
      connectionId: this.getOptimalConnection()
    };

    this.emit('marketData', enrichedMarketData);
  }

  updateLatencyMetrics(latency) {
    // Exponential moving average for latency
    if (this.performanceMetrics.averageLatency === 0) {
      this.performanceMetrics.averageLatency = latency;
    } else {
      this.performanceMetrics.averageLatency =
        (this.performanceMetrics.averageLatency * 0.9) + (latency * 0.1);
    }
  }

  updatePerformanceMetrics(metrics) {
    Object.assign(this.performanceMetrics, metrics);
    this.emit('performanceUpdate', this.performanceMetrics);
  }

  getOptimalConnection() {
    // Select connection with lowest load
    let optimalConnection = null;
    let lowestLoad = Infinity;

    this.connections.forEach((conn, id) => {
      if (conn.active) {
        const load = conn.metrics.requests / (Date.now() - conn.lastUsed);
        if (load < lowestLoad) {
          lowestLoad = load;
          optimalConnection = id;
        }
      }
    });

    return optimalConnection || Array.from(this.connections.keys())[0];
  }

  startDataStreaming() {
    logger.info('Starting MT5 data streaming...');

    // Send command to Python bridge to start streaming
    if (this.pythonProcess && this.pythonProcess.stdin) {
      const streamingConfig = {
        symbols: this.config.symbols || ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
        timeframes: this.config.timeframes || ['M1', 'M5', 'M15'],
        targetTPS: this.config.targetTicksPerSecond || 50
      };

      const command = `START_STREAMING:${JSON.stringify(streamingConfig)}\n`;
      this.pythonProcess.stdin.write(command);
    }
  }

  async reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      throw new Error('Maximum reconnection attempts reached');
    }

    this.reconnectAttempts++;
    logger.info(`Reconnecting to MT5 (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    try {
      await this.disconnect();

      // Wait before reconnecting
      await new Promise(resolve => setTimeout(resolve, this.reconnectDelay));

      await this.connect();

    } catch (error) {
      logger.error('Reconnection failed:', error);

      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 60000);
      throw error;
    }
  }

  async disconnect() {
    logger.info('Disconnecting from MetaTrader 5...');

    this.isConnected = false;
    this.isShuttingDown = true;

    try {
      // Stop Python bridge
      if (this.pythonProcess) {
        this.pythonProcess.stdin.write('STOP\n');

        // Wait for graceful shutdown
        await new Promise((resolve) => {
          const timer = setTimeout(() => {
            this.pythonProcess.kill('SIGTERM');
            resolve();
          }, 5000);

          this.pythonProcess.on('close', () => {
            clearTimeout(timer);
            resolve();
          });
        });

        this.pythonProcess = null;
      }

      // Close connection pool
      this.connections.clear();

      logger.info('MT5 disconnected successfully');
      this.emit('disconnected');

    } catch (error) {
      logger.error('Error during MT5 disconnection:', error);
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
    return this.isConnected && this.connections.size > 0;
  }

  getConnectionCount() {
    return Array.from(this.connections.values()).filter(conn => conn.active).length;
  }

  getPerformanceMetrics() {
    const uptime = Date.now() - this.performanceMetrics.startTime;
    const ticksPerSecond = this.performanceMetrics.ticksProcessed / (uptime / 1000);

    return {
      ...this.performanceMetrics,
      uptime,
      ticksPerSecond: Math.round(ticksPerSecond * 100) / 100,
      connectionCount: this.getConnectionCount(),
      reconnectAttempts: this.reconnectAttempts
    };
  }

  getConnectionStatus() {
    const connections = Array.from(this.connections.entries()).map(([id, conn]) => ({
      id,
      active: conn.active,
      lastUsed: conn.lastUsed,
      metrics: conn.metrics
    }));

    return {
      totalConnections: this.connections.size,
      activeConnections: connections.filter(c => c.active).length,
      connections
    };
  }

  // Trading interface methods (for future expansion)
  async sendOrder(orderData) {
    if (!this.isConnected) {
      throw new Error('MT5 not connected');
    }

    const command = `SEND_ORDER:${JSON.stringify(orderData)}\n`;
    if (this.pythonProcess && this.pythonProcess.stdin) {
      this.pythonProcess.stdin.write(command);
    }
  }

  async getAccountInfo() {
    if (!this.isConnected) {
      throw new Error('MT5 not connected');
    }

    return new Promise((resolve, reject) => {
      const command = `GET_ACCOUNT\n`;

      const onAccountInfo = (data) => {
        resolve(data);
        this.removeListener('accountInfo', onAccountInfo);
      };

      this.on('accountInfo', onAccountInfo);

      if (this.pythonProcess && this.pythonProcess.stdin) {
        this.pythonProcess.stdin.write(command);
      }

      // Timeout after 10 seconds
      setTimeout(() => {
        this.removeListener('accountInfo', onAccountInfo);
        reject(new Error('Account info request timeout'));
      }, 10000);
    });
  }
}

module.exports = MetaTraderConnector;