#!/usr/bin/env node
/**
 * Simplified Trading Engine Server
 * Core functionality with stable startup
 */

require('dotenv').config();

const express = require('express');
const http = require('http');
const cors = require('cors');
const winston = require('winston');

// Core services
const OrderExecutor = require('./services/OrderExecutor');
const AISignalIntegration = require('./services/AISignalIntegration');
const TradingMetrics = require('./services/TradingMetrics');
const ExternalAPIManager = require('./services/ExternalAPIManager');
const FlowRegistryClient = require('./services/FlowRegistryClient');

// Logger setup
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.colorize(),
    winston.format.simple()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

class SimpleTradingEngineServer {
  constructor() {
    this.serviceName = 'trading-engine';
    this.version = '2.0.0';
    this.port = process.env.PORT || 9010;
    this.logger = logger;

    // Express app
    this.app = express();
    this.server = http.createServer(this.app);

    this.setupMiddleware();
    this.initializeServices();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(cors({
      origin: (process.env.CORS_ORIGINS || '').split(',').filter(Boolean),
      credentials: true
    }));
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));
  }

  initializeServices() {
    try {
      // Initialize core services
      this.orderExecutor = new OrderExecutor({
        targetLatency: parseInt(process.env.TARGET_LATENCY) || 10,
        maxLatency: parseInt(process.env.MAX_LATENCY) || 50,
        circuitBreakerThreshold: parseInt(process.env.CIRCUIT_BREAKER_THRESHOLD) || 10,
        logger: this.logger
      });

      this.aiSignalIntegration = new AISignalIntegration({
        aiOrchestratorUrl: process.env.AI_ORCHESTRATOR_URL || 'http://localhost:8020',
        logger: this.logger
      });

      this.tradingMetrics = new TradingMetrics({
        metricsInterval: parseInt(process.env.METRICS_COLLECTION_INTERVAL) || 5000,
        logger: this.logger
      });

      this.externalAPIManager = new ExternalAPIManager({
        binanceApiKey: process.env.BINANCE_API_KEY,
        binanceSecretKey: process.env.BINANCE_SECRET_KEY,
        coinbaseApiKey: process.env.COINBASE_API_KEY,
        coinbaseSecretKey: process.env.COINBASE_SECRET_KEY,
        logger: this.logger
      });

      this.flowRegistryClient = new FlowRegistryClient({
        configServiceUrl: process.env.CONFIG_SERVICE_URL || 'http://localhost:8012',
        flowTrackingEnabled: process.env.FEATURE_FLOW_REGISTRY_TRACKING === 'true',
        logger: this.logger
      });

      this.logger.info('Core services initialized successfully', {
        service: this.serviceName
      });

    } catch (error) {
      this.logger.error('Failed to initialize services', {
        service: this.serviceName,
        error: error.message
      });
      throw error;
    }
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      const health = {
        status: 'healthy',
        service: this.serviceName,
        version: this.version,
        timestamp: new Date().toISOString(),
        port: this.port,
        services: {
          orderExecutor: 'active',
          aiSignalIntegration: this.aiSignalIntegration.isHealthy() ? 'active' : 'degraded',
          tradingMetrics: this.tradingMetrics.isHealthy() ? 'active' : 'degraded',
          externalAPIManager: this.externalAPIManager.isHealthy() ? 'active' : 'degraded',
          flowRegistryClient: this.flowRegistryClient.isHealthy() ? 'active' : 'degraded'
        },
        features: {
          aiSignalIntegration: process.env.FEATURE_AI_SIGNAL_INTEGRATION === 'true',
          flowRegistryTracking: process.env.FEATURE_FLOW_REGISTRY_TRACKING === 'true',
          realTimeTrading: process.env.FEATURE_REAL_TIME_TRADING === 'true'
        }
      };

      res.json(health);
    });

    // Trading endpoints
    this.app.post('/api/orders/execute', async (req, res) => {
      const startTime = Date.now();
      let flowId = null;

      try {
        const order = req.body;
        const { userId, tenantId } = req.query;

        // Start flow tracking
        const flowResult = await this.flowRegistryClient.startFlow({
          name: 'Order Execution',
          description: `Execute ${order.side} order for ${order.symbol}`,
          type: 'trade-execution',
          instrument: order.symbol,
          orderType: order.type,
          userId,
          tenantId,
          metadata: {
            orderId: order.id,
            originalOrder: order
          }
        });

        flowId = flowResult.flowId;

        // Execute order
        const result = await this.orderExecutor.executeOrder({
          ...order,
          flowId,
          userId,
          tenantId
        });

        const executionTime = Date.now() - startTime;

        // Record metrics
        this.tradingMetrics.recordOrderExecution({
          orderId: result.orderId || order.id,
          instrument: order.symbol,
          executionTime,
          latency: result.latency || executionTime,
          volume: parseFloat(order.quantity || 0),
          success: result.success !== false
        });

        // Complete flow tracking
        if (flowId) {
          await this.flowRegistryClient.completeFlow(flowId, {
            success: result.success !== false,
            message: result.success !== false ? 'Order executed successfully' : (result.error || 'Unknown error'),
            data: result
          }, {
            executionTime,
            orderResult: result
          });
        }

        res.json({
          success: true,
          data: {
            ...result,
            flowId,
            executionTime: `${executionTime}ms`,
            performance: {
              latency: `${result.latency || executionTime}ms`,
              targetCompliance: (result.latency || executionTime) < 10 ? 'PASSED' : 'WARNING'
            }
          }
        });

      } catch (error) {
        const executionTime = Date.now() - startTime;

        // Record failed order
        this.tradingMetrics.recordOrderExecution({
          orderId: req.body.id,
          instrument: req.body.symbol,
          executionTime,
          latency: executionTime,
          volume: parseFloat(req.body.quantity || 0),
          success: false
        });

        // Record error
        this.tradingMetrics.recordError({
          type: 'order_execution_error',
          message: error.message
        });

        // Complete flow with error
        if (flowId) {
          await this.flowRegistryClient.completeFlow(flowId, {
            success: false,
            message: error.message,
            error: error.message
          });
        }

        this.logger.error('Order execution failed', {
          service: this.serviceName,
          error: error.message,
          orderId: req.body.id
        });

        res.status(500).json({
          success: false,
          error: error.message,
          flowId,
          executionTime: `${executionTime}ms`
        });
      }
    });

    // AI signals endpoint
    this.app.post('/api/ai/signals', async (req, res) => {
      try {
        const { instruments, timeframe, userId, tenantId } = req.body;

        const signals = await this.aiSignalIntegration.requestTradingSignals(
          instruments || ['BTCUSD'],
          timeframe || '1m',
          userId,
          tenantId
        );

        res.json({
          success: true,
          data: signals
        });

      } catch (error) {
        this.logger.error('AI signals request failed', {
          service: this.serviceName,
          error: error.message
        });

        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Metrics endpoint
    this.app.get('/api/metrics', (req, res) => {
      try {
        const metrics = {
          trading: this.tradingMetrics.getSnapshot(),
          ai: this.aiSignalIntegration.getMetrics(),
          flow: this.flowRegistryClient.getMetrics(),
          external: this.externalAPIManager.getMetrics()
        };

        res.json({
          success: true,
          data: metrics
        });

      } catch (error) {
        this.logger.error('Metrics request failed', {
          service: this.serviceName,
          error: error.message
        });

        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Market data endpoints
    this.app.get('/api/market/:symbol', async (req, res) => {
      try {
        const { symbol } = req.params;
        const { exchange = 'binance' } = req.query;

        let marketData;
        if (exchange === 'binance') {
          marketData = await this.externalAPIManager.getBinanceMarketData(symbol);
        } else if (exchange === 'coinbase') {
          marketData = await this.externalAPIManager.getCoinbaseMarketData(symbol);
        } else {
          throw new Error(`Unsupported exchange: ${exchange}`);
        }

        res.json({
          success: true,
          data: marketData
        });

      } catch (error) {
        this.logger.error('Market data request failed', {
          service: this.serviceName,
          error: error.message,
          symbol: req.params.symbol
        });

        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });
  }

  async start() {
    const port = this.port;
    const host = process.env.HOST || '0.0.0.0';

    try {
      await new Promise((resolve, reject) => {
        this.server.listen(port, host, (err) => {
          if (err) {
            reject(err);
            return;
          }

          this.logger.info('Trading Engine Server started successfully', {
            service: this.serviceName,
            port,
            host,
            version: this.version,
            environment: process.env.NODE_ENV || 'development',
            targetLatency: `${process.env.TARGET_LATENCY || 10}ms`,
            features: {
              aiSignalIntegration: process.env.FEATURE_AI_SIGNAL_INTEGRATION === 'true',
              flowRegistryTracking: process.env.FEATURE_FLOW_REGISTRY_TRACKING === 'true',
              realTimeTrading: process.env.FEATURE_REAL_TIME_TRADING === 'true'
            }
          });

          resolve();
        });
      });

      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());

    } catch (error) {
      this.logger.error('Failed to start Trading Engine Server', {
        service: this.serviceName,
        error: error.message || 'Unknown error',
        stack: error.stack || 'No stack available'
      });
      throw error;
    }
  }

  async shutdown() {
    this.logger.info('Shutting down Trading Engine Server...', {
      service: this.serviceName
    });

    // Stop services
    if (this.tradingMetrics) {
      this.tradingMetrics.stopCollection();
    }

    // Close server
    this.server.close(() => {
      this.logger.info('Trading Engine Server shutdown complete', {
        service: this.serviceName
      });
      process.exit(0);
    });
  }
}

// Start server if this file is run directly
if (require.main === module) {
  const server = new SimpleTradingEngineServer();
  server.start().catch((error) => {
    logger.error('Failed to start server', {
      error: error.message || 'Unknown error',
      stack: error.stack || 'No stack available'
    });
    process.exit(1);
  });
}

module.exports = SimpleTradingEngineServer;