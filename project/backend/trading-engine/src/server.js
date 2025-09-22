const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const logger = require('./utils/logger');
const OrderExecutor = require('./services/OrderExecutor');
const CorrelationAnalyzer = require('./services/CorrelationAnalyzer');
const SessionManager = require('./services/SessionManager');
const IslamicTradingService = require('./services/IslamicTradingService');

class TradingEngineServer {
  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.wss = null;
    this.clients = new Map();
    
    // Trading services
    this.orderExecutor = new OrderExecutor({
      targetLatency: 10, // 10ms target
      maxLatency: 50,
      redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379
      }
    });
    
    this.correlationAnalyzer = new CorrelationAnalyzer({
      updateInterval: 30000, // 30 seconds
      historyLength: 200,
      correlationThreshold: 0.7
    });
    
    this.sessionManager = new SessionManager({
      checkInterval: 60000, // 1 minute
      preSessionAlert: 300000 // 5 minutes
    });
    
    this.islamicTradingService = new IslamicTradingService({
      enabled: true
    });
    
    this.setupEventListeners();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocket();
  }

  /**
   * Setup event listeners for trading services
   */
  setupEventListeners() {
    // Order execution events
    this.orderExecutor.on('orderExecuted', (data) => {
      logger.order.executed(data.orderId, data.execution, data.latency);
      this.broadcastToClients({
        type: 'order_executed',
        data
      });
    });
    
    this.orderExecutor.on('orderFailed', (data) => {
      logger.order.failed(data.orderId, { message: data.error }, data.latency);
      this.broadcastToClients({
        type: 'order_failed',
        data
      });
    });
    
    this.orderExecutor.on('performanceAlert', (data) => {
      logger.performance.alert(data.type, 'latency', data.target, data.latency);
      this.broadcastToClients({
        type: 'performance_alert',
        data
      });
    });
    
    // Correlation events
    this.correlationAnalyzer.on('highCorrelation', (data) => {
      logger.correlation.alert(data.symbol1, data.symbol2, data.correlation, this.correlationAnalyzer.correlationThreshold);
      this.broadcastToClients({
        type: 'high_correlation',
        data
      });
    });
    
    this.correlationAnalyzer.on('correlationChange', (data) => {
      this.broadcastToClients({
        type: 'correlation_change',
        data
      });
    });
    
    // Session events
    this.sessionManager.on('sessionStart', (data) => {
      logger.session.start(data.session.name, data.session.characteristics);
      this.broadcastToClients({
        type: 'session_start',
        data
      });
    });
    
    this.sessionManager.on('sessionEnd', (data) => {
      logger.session.end(data.session.name, {});
      this.broadcastToClients({
        type: 'session_end',
        data
      });
    });
    
    this.sessionManager.on('sessionAlert', (data) => {
      this.broadcastToClients({
        type: 'session_alert',
        data
      });
    });
    
    // Islamic trading events
    this.islamicTradingService.on('islamicAccountRegistered', (data) => {
      logger.islamic.validation(data.accountId, true, []);
      this.broadcastToClients({
        type: 'islamic_account_registered',
        data
      });
    });
  }

  /**
   * Setup Express middleware
   */
  setupMiddleware() {
    this.app.use(helmet());
    this.app.use(compression());
    this.app.use(cors({
      origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true
    }));
    
    // Rate limiting for order endpoints
    const orderLimiter = rateLimit({
      windowMs: 1000, // 1 second
      max: 100, // 100 requests per second
      message: 'Too many order requests, please try again later'
    });
    
    const generalLimiter = rateLimit({
      windowMs: 60 * 1000, // 1 minute
      max: 1000, // 1000 requests per minute
      message: 'Too many requests, please try again later'
    });
    
    this.app.use('/api/orders', orderLimiter);
    this.app.use('/api', generalLimiter);
    
    this.app.use(express.json({ limit: '1mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    
    // Request logging
    this.app.use((req, res, next) => {
      const startTime = Date.now();
      res.on('finish', () => {
        const latency = Date.now() - startTime;
        logger.info('HTTP Request', {
          method: req.method,
          url: req.url,
          status: res.statusCode,
          latency,
          ip: req.ip
        });
      });
      next();
    });
  }

  /**
   * Setup API routes
   */
  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      const health = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: process.env.npm_package_version || '1.0.0',
        services: {
          orderExecutor: {
            status: 'active',
            metrics: this.orderExecutor.getPerformanceMetrics()
          },
          correlationAnalyzer: {
            status: 'active',
            statistics: this.correlationAnalyzer.getStatistics()
          },
          sessionManager: {
            status: 'active',
            currentSession: this.sessionManager.getCurrentSession(),
            nextSession: this.sessionManager.getNextSession()
          },
          islamicTrading: {
            status: 'active',
            statistics: this.islamicTradingService.getStatistics()
          }
        }
      };
      
      res.json(health);
    });
    
    // Order execution endpoints
    this.app.post('/api/orders/execute', async (req, res) => {
      try {
        const order = req.body;
        const result = await this.orderExecutor.executeOrder(order);
        
        res.json({
          success: true,
          data: result
        });
      } catch (error) {
        logger.error('Order execution failed', { error: error.message, order: req.body });
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    });
    
    this.app.get('/api/orders/performance', (req, res) => {
      const metrics = this.orderExecutor.getPerformanceMetrics();
      res.json({
        success: true,
        data: metrics
      });
    });
    
    // Correlation analysis endpoints
    this.app.get('/api/correlation/matrix', (req, res) => {
      const matrix = this.correlationAnalyzer.getCorrelationMatrix();
      res.json({
        success: true,
        data: matrix
      });
    });
    
    this.app.get('/api/correlation/:symbol', (req, res) => {
      const { symbol } = req.params;
      const correlations = this.correlationAnalyzer.getSymbolCorrelations(symbol);
      res.json({
        success: true,
        data: correlations
      });
    });
    
    this.app.get('/api/correlation/forex-gold', (req, res) => {
      const analysis = this.correlationAnalyzer.getForexGoldCorrelation();
      res.json({
        success: true,
        data: analysis
      });
    });
    
    // Session management endpoints
    this.app.get('/api/sessions/current', (req, res) => {
      const session = this.sessionManager.getCurrentSession();
      const overlaps = this.sessionManager.getSessionOverlaps();
      res.json({
        success: true,
        data: {
          currentSession: session,
          overlaps
        }
      });
    });
    
    this.app.get('/api/sessions/recommendations', (req, res) => {
      const recommendations = this.sessionManager.getSessionRecommendations();
      res.json({
        success: true,
        data: recommendations
      });
    });
    
    this.app.get('/api/sessions/statistics', (req, res) => {
      const statistics = this.sessionManager.getSessionStatistics();
      res.json({
        success: true,
        data: statistics
      });
    });
    
    // Islamic trading endpoints
    this.app.post('/api/islamic/register', async (req, res) => {
      try {
        const { accountId, ...accountDetails } = req.body;
        const islamicAccount = this.islamicTradingService.registerIslamicAccount(accountId, accountDetails);
        
        res.json({
          success: true,
          data: islamicAccount
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    });
    
    this.app.post('/api/islamic/validate-trade', async (req, res) => {
      try {
        const { accountId, tradeRequest } = req.body;
        const validation = this.islamicTradingService.validateTrade(accountId, tradeRequest);
        
        res.json({
          success: true,
          data: validation
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    });
    
    this.app.get('/api/islamic/compliance-report/:accountId', async (req, res) => {
      try {
        const { accountId } = req.params;
        const { period = 30 } = req.query;
        const report = this.islamicTradingService.generateComplianceReport(accountId, parseInt(period));
        
        res.json({
          success: true,
          data: report
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          error: error.message
        });
      }
    });
    
    this.app.get('/api/islamic/statistics', (req, res) => {
      const statistics = this.islamicTradingService.getStatistics();
      res.json({
        success: true,
        data: statistics
      });
    });
    
    // Market data simulation endpoint
    this.app.post('/api/market-data/simulate', (req, res) => {
      const { symbol, price, timestamp } = req.body;
      
      // Add price data to correlation analyzer
      this.correlationAnalyzer.addPriceData(symbol, price, timestamp);
      
      res.json({
        success: true,
        message: 'Market data added to correlation analysis'
      });
    });
    
    // Error handling
    this.app.use((err, req, res, next) => {
      logger.error('Unhandled error', {
        error: err.message,
        stack: err.stack,
        url: req.url,
        method: req.method
      });
      
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    });
    
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        success: false,
        error: 'Endpoint not found'
      });
    });
  }

  /**
   * Setup WebSocket server
   */
  setupWebSocket() {
    this.wss = new WebSocket.Server({
      server: this.server,
      path: '/ws'
    });
    
    this.wss.on('connection', (ws, req) => {
      const clientId = uuidv4();
      const client = {
        id: clientId,
        ws,
        subscriptions: new Set(),
        lastPing: Date.now(),
        ip: req.socket.remoteAddress
      };
      
      this.clients.set(clientId, client);
      
      logger.info('WebSocket client connected', {
        clientId,
        ip: client.ip,
        totalClients: this.clients.size
      });
      
      // Send welcome message
      ws.send(JSON.stringify({
        type: 'welcome',
        clientId,
        timestamp: Date.now()
      }));
      
      // Handle messages
      ws.on('message', (data) => {
        this.handleWebSocketMessage(clientId, data);
      });
      
      // Handle disconnect
      ws.on('close', () => {
        this.clients.delete(clientId);
        logger.info('WebSocket client disconnected', {
          clientId,
          totalClients: this.clients.size
        });
      });
      
      // Handle errors
      ws.on('error', (error) => {
        logger.error('WebSocket error', {
          clientId,
          error: error.message
        });
        this.clients.delete(clientId);
      });
    });
    
    // Ping clients periodically
    setInterval(() => {
      this.pingClients();
    }, 30000);
  }

  /**
   * Handle WebSocket messages
   */
  handleWebSocketMessage(clientId, data) {
    try {
      const message = JSON.parse(data.toString());
      const client = this.clients.get(clientId);
      
      if (!client) return;
      
      switch (message.type) {
        case 'subscribe':
          client.subscriptions.add(message.channel);
          client.ws.send(JSON.stringify({
            type: 'subscribed',
            channel: message.channel,
            timestamp: Date.now()
          }));
          break;
          
        case 'unsubscribe':
          client.subscriptions.delete(message.channel);
          client.ws.send(JSON.stringify({
            type: 'unsubscribed',
            channel: message.channel,
            timestamp: Date.now()
          }));
          break;
          
        case 'ping':
          client.lastPing = Date.now();
          client.ws.send(JSON.stringify({
            type: 'pong',
            timestamp: Date.now()
          }));
          break;
          
        default:
          client.ws.send(JSON.stringify({
            type: 'error',
            message: 'Unknown message type',
            timestamp: Date.now()
          }));
      }
    } catch (error) {
      logger.error('Error handling WebSocket message', {
        clientId,
        error: error.message
      });
    }
  }

  /**
   * Broadcast message to all clients
   */
  broadcastToClients(message, channel = null) {
    this.clients.forEach((client) => {
      if (client.ws.readyState === WebSocket.OPEN) {
        if (!channel || client.subscriptions.has(channel)) {
          client.ws.send(JSON.stringify({
            ...message,
            timestamp: Date.now()
          }));
        }
      }
    });
  }

  /**
   * Ping clients to check connectivity
   */
  pingClients() {
    const now = Date.now();
    this.clients.forEach((client, clientId) => {
      if (now - client.lastPing > 60000) { // 1 minute timeout
        client.ws.close();
        this.clients.delete(clientId);
      } else if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.ping();
      }
    });
  }

  /**
   * Start the trading engine server
   */
  async start() {
    const port = process.env.PORT || 3005;
    const host = process.env.HOST || '0.0.0.0';
    
    try {
      // Create logs directory
      const fs = require('fs');
      const logsDir = require('path').join(__dirname, '../logs');
      if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
      }
      
      this.server.listen(port, host, () => {
        logger.info('Trading Engine Server started', {
          port,
          host,
          environment: process.env.NODE_ENV || 'development',
          targetLatency: this.orderExecutor.targetLatency,
          services: {
            orderExecutor: 'active',
            correlationAnalyzer: 'active',
            sessionManager: 'active',
            islamicTrading: 'active'
          }
        });
      });
      
      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());
      
    } catch (error) {
      logger.error('Failed to start Trading Engine Server', { error: error.message });
      process.exit(1);
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown() {
    logger.info('Shutting down Trading Engine Server...');
    
    // Close WebSocket connections
    this.clients.forEach((client) => {
      client.ws.close();
    });
    
    // Stop services
    this.correlationAnalyzer.stop();
    this.sessionManager.stop();
    
    // Close server
    this.server.close(() => {
      logger.info('Trading Engine Server shutdown complete');
      process.exit(0);
    });
  }
}

// Start server if this file is run directly
if (require.main === module) {
  const server = new TradingEngineServer();
  server.start().catch((error) => {
    logger.error('Failed to start server', { error: error.message });
    process.exit(1);
  });
}

module.exports = TradingEngineServer;