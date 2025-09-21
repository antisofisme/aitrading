const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { createServer } = require('http');

const config = require('../config/config');
const logger = require('./utils/logger');
const { validateConnection } = require('./middleware/validation');
const MT5Service = require('./services/mt5-service');
const DataController = require('./controllers/data-controller');

class DataBridgeServer {
  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.wss = null;
    this.mt5Service = new MT5Service();
    this.dataController = new DataController();
    this.clients = new Map();

    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocket();
  }

  setupMiddleware() {
    this.app.use(helmet());
    this.app.use(compression());
    this.app.use(cors({
      origin: config.cors.allowedOrigins,
      credentials: true
    }));
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });
      next();
    });
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version,
        uptime: process.uptime(),
        mt5Connected: this.mt5Service.isConnected()
      });
    });

    // API routes
    this.app.get('/api/status', this.dataController.getStatus.bind(this.dataController));
    this.app.get('/api/symbols', this.dataController.getSymbols.bind(this.dataController));
    this.app.get('/api/market-data/:symbol', this.dataController.getMarketData.bind(this.dataController));

    // Error handling
    this.app.use((err, req, res, next) => {
      logger.error('Unhandled error:', err);
      res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
      });
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({ error: 'Route not found' });
    });
  }

  setupWebSocket() {
    this.wss = new WebSocket.Server({
      server: this.server,
      path: '/ws',
      verifyClient: (info) => {
        return validateConnection(info);
      }
    });

    this.wss.on('connection', (ws, req) => {
      const clientId = this.generateClientId();
      this.clients.set(clientId, {
        ws,
        subscriptions: new Set(),
        lastPing: Date.now(),
        ip: req.socket.remoteAddress
      });

      logger.info(`WebSocket client connected: ${clientId}`);

      ws.on('message', (data) => {
        this.handleWebSocketMessage(clientId, data);
      });

      ws.on('close', () => {
        this.clients.delete(clientId);
        logger.info(`WebSocket client disconnected: ${clientId}`);
      });

      ws.on('error', (error) => {
        logger.error(`WebSocket error for client ${clientId}:`, error);
        this.clients.delete(clientId);
      });

      // Send welcome message
      this.sendToClient(clientId, {
        type: 'welcome',
        clientId,
        timestamp: new Date().toISOString()
      });
    });

    // Ping clients every 30 seconds
    setInterval(() => {
      this.pingClients();
    }, 30000);
  }

  handleWebSocketMessage(clientId, data) {
    try {
      const message = JSON.parse(data.toString());
      logger.debug(`Message from ${clientId}:`, message);

      switch (message.type) {
        case 'subscribe':
          this.handleSubscription(clientId, message);
          break;
        case 'unsubscribe':
          this.handleUnsubscription(clientId, message);
          break;
        case 'ping':
          this.handlePing(clientId);
          break;
        default:
          this.sendToClient(clientId, {
            type: 'error',
            message: 'Unknown message type'
          });
      }
    } catch (error) {
      logger.error(`Error parsing message from ${clientId}:`, error);
      this.sendToClient(clientId, {
        type: 'error',
        message: 'Invalid message format'
      });
    }
  }

  handleSubscription(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    const { symbol, dataType } = message;
    if (!symbol || !dataType) {
      this.sendToClient(clientId, {
        type: 'error',
        message: 'Symbol and dataType are required for subscription'
      });
      return;
    }

    const subscription = `${symbol}:${dataType}`;
    client.subscriptions.add(subscription);

    this.sendToClient(clientId, {
      type: 'subscribed',
      symbol,
      dataType,
      timestamp: new Date().toISOString()
    });

    logger.info(`Client ${clientId} subscribed to ${subscription}`);
  }

  handleUnsubscription(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    const { symbol, dataType } = message;
    const subscription = `${symbol}:${dataType}`;
    client.subscriptions.delete(subscription);

    this.sendToClient(clientId, {
      type: 'unsubscribed',
      symbol,
      dataType,
      timestamp: new Date().toISOString()
    });

    logger.info(`Client ${clientId} unsubscribed from ${subscription}`);
  }

  handlePing(clientId) {
    const client = this.clients.get(clientId);
    if (!client) return;

    client.lastPing = Date.now();
    this.sendToClient(clientId, {
      type: 'pong',
      timestamp: new Date().toISOString()
    });
  }

  sendToClient(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client || client.ws.readyState !== WebSocket.OPEN) return;

    try {
      client.ws.send(JSON.stringify(message));
    } catch (error) {
      logger.error(`Error sending message to client ${clientId}:`, error);
      this.clients.delete(clientId);
    }
  }

  broadcast(message, filter = null) {
    this.clients.forEach((client, clientId) => {
      if (filter && !filter(client)) return;
      this.sendToClient(clientId, message);
    });
  }

  pingClients() {
    const now = Date.now();
    this.clients.forEach((client, clientId) => {
      if (now - client.lastPing > 60000) { // 1 minute timeout
        logger.warn(`Client ${clientId} timed out`);
        client.ws.close();
        this.clients.delete(clientId);
      }
    });
  }

  generateClientId() {
    return require('uuid').v4();
  }

  async start() {
    try {
      // Initialize MT5 service
      await this.mt5Service.initialize();

      this.server.listen(config.server.port, config.server.host, () => {
        logger.info(`Data Bridge Server started on ${config.server.host}:${config.server.port}`);
        logger.info(`WebSocket endpoint: ws://${config.server.host}:${config.server.port}/ws`);
      });

      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());

    } catch (error) {
      logger.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  async shutdown() {
    logger.info('Shutting down Data Bridge Server...');

    // Close WebSocket connections
    this.clients.forEach((client, clientId) => {
      client.ws.close();
    });

    // Close MT5 connection
    await this.mt5Service.disconnect();

    // Close HTTP server
    this.server.close(() => {
      logger.info('Server shutdown complete');
      process.exit(0);
    });
  }
}

// Start server if this file is run directly
if (require.main === module) {
  const server = new DataBridgeServer();
  server.start().catch(error => {
    logger.error('Failed to start server:', error);
    process.exit(1);
  });
}

module.exports = DataBridgeServer;