const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const logger = require('./utils/logger');
const OrderExecutor = require('./services/OrderExecutor');
const CorrelationAnalyzer = require('./services/CorrelationAnalyzer');
const SessionManager = require('./services/SessionManager');
const IslamicTradingService = require('./services/IslamicTradingService');
const AISignalIntegration = require('./services/AISignalIntegration');
const FlowRegistryClient = require('./services/FlowRegistryClient');
const TradingMetrics = require('./services/TradingMetrics');
const ExternalAPIManager = require('./services/ExternalAPIManager');

class TradingEngineServer {
  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.wss = null;
    this.clients = new Map();
    this.serviceName = 'trading-engine';
    this.port = process.env.PORT || 9000;
    this.version = '1.0.0';
    
    // Trading services with Plan2 integration
    this.orderExecutor = new OrderExecutor({
      targetLatency: parseInt(process.env.TARGET_LATENCY) || 10, // 10ms target
      maxLatency: parseInt(process.env.MAX_LATENCY) || 50,
      redis: {
        host: process.env.DRAGONFLY_HOST || 'localhost',
        port: process.env.DRAGONFLY_PORT || 6379,
        password: process.env.DRAGONFLY_PASSWORD
      }
    });

    // AI Signal Integration (Port 8020)
    this.aiSignalIntegration = new AISignalIntegration({
      aiOrchestratorUrl: process.env.AI_ORCHESTRATOR_URL || 'http://localhost:8020',
      logger: logger
    });

    // Flow Registry Client (Port 8012)
    this.flowRegistryClient = new FlowRegistryClient({
      configServiceUrl: process.env.CONFIG_SERVICE_URL || 'http://localhost:8012',
      logger: logger,
      flowTrackingEnabled: process.env.FLOW_TRACKING_ENABLED === 'true'
    });

    // Trading Metrics Service
    this.tradingMetrics = new TradingMetrics({
      logger: logger,
      metricsInterval: parseInt(process.env.METRICS_COLLECTION_INTERVAL) || 5000
    });

    // External API Manager (Binance, etc.)
    this.externalAPIManager = new ExternalAPIManager({
      binanceApiKey: process.env.BINANCE_API_KEY,
      binanceSecretKey: process.env.BINANCE_SECRET_KEY,
      coinbaseApiKey: process.env.COINBASE_API_KEY,
      coinbaseSecretKey: process.env.COINBASE_SECRET_KEY,
      logger: logger
    });
    
    this.correlationAnalyzer = new CorrelationAnalyzer({
      updateInterval: parseInt(process.env.CORRELATION_UPDATE_INTERVAL) || 30000,
      historyLength: parseInt(process.env.CORRELATION_HISTORY_LENGTH) || 200,
      correlationThreshold: parseFloat(process.env.CORRELATION_THRESHOLD) || 0.7
    });
    
    this.sessionManager = new SessionManager({
      checkInterval: parseInt(process.env.SESSION_CHECK_INTERVAL) || 60000,
      preSessionAlert: parseInt(process.env.PRE_SESSION_ALERT) || 300000
    });
    
    this.islamicTradingService = new IslamicTradingService({
      enabled: process.env.ISLAMIC_TRADING_ENABLED === 'true',
      swapFreeEnabled: process.env.SWAP_FREE_ENABLED === 'true',
      shariahCompliant: process.env.SHARIAH_COMPLIANT === 'true'
    });

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      orderCount: 0,
      aiSignalCount: 0,
      flowRegistryEvents: 0,
      averageLatency: 0,
      lastHealthCheck: Date.now(),
      tradingVolume: 0,
      successfulTrades: 0,
      failedTrades: 0
    };

    // Integration status tracking
    this.integrationStatus = {
      aiOrchestrator: { status: 'unknown', lastCheck: null },
      configService: { status: 'unknown', lastCheck: null },
      databaseService: { status: 'unknown', lastCheck: null },
      orderManagement: { status: 'unknown', lastCheck: null },
      riskAnalyzer: { status: 'unknown', lastCheck: null },
      portfolioManager: { status: 'unknown', lastCheck: null }
    };
    
    this.setupEventListeners();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocket();
  }

  /**
   * Setup event listeners for trading services
   */
  setupEventListeners() {
    // AI Signal Integration events
    this.aiSignalIntegration.on('signalsReceived', (data) => {
      this.tradingMetrics.recordAISignal({
        signalId: data.signals[0]?.timestamp,
        signalCount: data.signals.length,
        accuracy: data.metadata?.aiAccuracy
      });
      this.broadcastToClients({
        type: 'ai_signals_received',
        data: {
          signalCount: data.signals.length,
          processingTime: data.processingTime,
          accuracy: data.metadata?.aiAccuracy
        }
      });
    });

    this.aiSignalIntegration.on('signalError', (data) => {
      this.tradingMetrics.recordError({
        type: 'ai_signal_error',
        message: data.error
      });
    });

    // Flow Registry events
    this.flowRegistryClient.on('flowStarted', (data) => {
      this.tradingMetrics.recordFlow({
        flowId: data.flowId,
        type: 'started'
      });
    });

    this.flowRegistryClient.on('flowCompleted', (data) => {
      this.tradingMetrics.recordFlow({
        flowId: data.flowId,
        type: 'completed',
        success: data.result.success,
        duration: data.duration,
        completed: true
      });
    });

    // External API events
    this.externalAPIManager.on('tradeExecuted', (data) => {
      this.broadcastToClients({
        type: 'trade_executed',
        data: {
          exchange: data.exchange,
          orderId: data.result.orderId,
          simulation: data.result.simulation
        }
      });
    });

    // Trading Metrics events
    this.tradingMetrics.on('metricsUpdated', (metrics) => {
      this.broadcastToClients({
        type: 'metrics_updated',
        data: metrics
      }, 'metrics');
    });
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
    // Enhanced health check with Plan2 integrations
    this.app.get('/health', async (req, res) => {
      try {
        // Check all service integrations
        const integrationChecks = await Promise.allSettled([
          this.checkServiceHealth('ai-orchestrator', process.env.AI_ORCHESTRATOR_PORT),
          this.checkServiceHealth('config-service', process.env.CONFIG_SERVICE_PORT),
          this.checkServiceHealth('database-service', process.env.DATABASE_SERVICE_PORT)
        ]);

        const [aiOrchestrator, configService, databaseService] = integrationChecks;

        this.updateIntegrationStatus('aiOrchestrator', aiOrchestrator.status === 'fulfilled');
        this.updateIntegrationStatus('configService', configService.status === 'fulfilled');
        this.updateIntegrationStatus('databaseService', databaseService.status === 'fulfilled');
        const health = {
          status: 'healthy',
          timestamp: new Date().toISOString(),
          uptime: process.uptime(),
          version: this.version,
          port: this.port,
          service: this.serviceName,
          level: 'trading-engine',
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
            },
            aiSignalIntegration: {
              status: this.aiSignalIntegration.isHealthy() ? 'active' : 'degraded',
              connection: this.aiSignalIntegration.getConnectionStatus(),
              metrics: this.aiSignalIntegration.getMetrics()
            },
            flowRegistryClient: {
              status: this.flowRegistryClient.isHealthy() ? 'active' : 'degraded',
              connection: this.flowRegistryClient.getConnectionStatus(),
              metrics: this.flowRegistryClient.getMetrics()
            },
            tradingMetrics: {
              status: this.tradingMetrics.isHealthy() ? 'active' : 'degraded',
              summary: this.tradingMetrics.getPerformanceSummary()
            },
            externalAPIManager: {
              status: this.externalAPIManager.isHealthy() ? 'active' : 'degraded',
              connections: this.externalAPIManager.getConnectionStatus(),
              metrics: this.externalAPIManager.getMetrics()
            }
          },
          integrations: this.integrationStatus,
          performance: {
            targetLatency: `${process.env.TARGET_LATENCY || 10}ms`,
            currentMetrics: this.tradingMetrics.getSnapshot(),
            overallStatus: this.tradingMetrics.getOverallStatus()
          },
          features: {
            aiSignalIntegration: process.env.FEATURE_AI_SIGNAL_INTEGRATION === 'true',
            flowRegistryTracking: process.env.FEATURE_FLOW_REGISTRY_TRACKING === 'true',
            realTimeTrading: process.env.FEATURE_REAL_TIME_TRADING === 'true',
            riskManagement: process.env.FEATURE_RISK_MANAGEMENT === 'true'
          }
        };

        // Determine overall health status
        const unhealthyServices = Object.values(health.services)
          .filter(service => service.status !== 'active').length;

        if (unhealthyServices > 0) {
          health.status = unhealthyServices > 3 ? 'unhealthy' : 'degraded';
        }

        res.status(health.status === 'unhealthy' ? 503 : 200).json(health);
      } catch (error) {
        this.logger.error('Health check failed', {
          error: error.message,
          stack: error.stack
        });

        res.status(500).json({
          status: 'error',
          message: 'Health check failed',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // Enhanced order execution with AI signals and flow tracking
    this.app.post('/api/orders/execute', async (req, res) => {
      const startTime = Date.now();
      let flowId = null;

      try {
        const order = req.body;
        const userId = req.headers['user-id'] || 'anonymous';
        const tenantId = req.headers['tenant-id'] || 'default';

        // Start flow tracking
        const flowResult = await this.flowRegistryClient.startFlow({
          name: `Order Execution - ${order.symbol || 'Unknown'}`,
          description: `Execute ${order.side} order for ${order.quantity} ${order.symbol}`,
          type: 'order-execution',
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

        // Execute order with enhanced tracking
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
            message: result.success !== false ? 'Order executed successfully' : result.error,
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
          error: error.message,
          order: req.body,
          executionTime: `${executionTime}ms`,
          flowId
        });

        res.status(400).json({
          success: false,
          error: error.message,
          flowId,
          executionTime: `${executionTime}ms`
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

    // =============================================================================
    // AI-DRIVEN TRADING ENDPOINTS (Plan2 Integration)
    // =============================================================================

    // Request AI trading signals
    this.app.post('/api/ai/signals/request', async (req, res) => {
      const startTime = Date.now();

      try {
        const { instruments, timeframe, userId, tenantId } = req.body;

        if (!instruments || !Array.isArray(instruments)) {
          return res.status(400).json({
            success: false,
            error: 'Instruments array is required'
          });
        }

        const signals = await this.aiSignalIntegration.requestTradingSignals(
          instruments,
          timeframe || '1m',
          userId || req.headers['user-id'],
          tenantId || req.headers['tenant-id']
        );

        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          data: {
            signals,
            metadata: {
              requestedInstruments: instruments.length,
              signalsGenerated: signals.length,
              processingTime: `${processingTime}ms`,
              timeframe,
              timestamp: new Date().toISOString()
            }
          }
        });

      } catch (error) {
        const processingTime = Date.now() - startTime;

        this.logger.error('AI signals request failed', {
          error: error.message,
          instruments: req.body.instruments,
          processingTime: `${processingTime}ms`
        });

        res.status(500).json({
          success: false,
          error: 'Failed to get AI signals',
          message: error.message,
          processingTime: `${processingTime}ms`
        });
      }
    });

    // Execute AI-driven trade
    this.app.post('/api/ai/trade/execute', async (req, res) => {
      const startTime = Date.now();
      let flowId = null;

      try {
        const { signal, riskParams, userId, tenantId } = req.body;

        if (!signal || !signal.instrument) {
          return res.status(400).json({
            success: false,
            error: 'Valid AI signal is required'
          });
        }

        // Start flow tracking for AI trade
        const flowResult = await this.flowRegistryClient.startFlow({
          name: `AI Trade - ${signal.instrument}`,
          description: `AI-driven ${signal.direction} trade for ${signal.instrument}`,
          type: 'ai-trade-execution',
          instrument: signal.instrument,
          orderType: 'ai-signal',
          userId: userId || req.headers['user-id'],
          tenantId: tenantId || req.headers['tenant-id'],
          metadata: {
            aiSignal: signal,
            riskParams,
            confidence: signal.confidence
          }
        });

        flowId = flowResult.flowId;

        // Create order from AI signal
        const order = {
          symbol: signal.instrument,
          side: signal.direction === 'long' ? 'BUY' : 'SELL',
          type: 'MARKET',
          quantity: this.calculatePositionSize(signal, riskParams),
          price: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          source: 'ai-signal',
          confidence: signal.confidence,
          flowId
        };

        // Execute the AI-driven trade
        const result = await this.orderExecutor.executeOrder(order);
        const executionTime = Date.now() - startTime;

        // Record AI signal action
        this.tradingMetrics.recordAISignal({
          signalId: signal.timestamp,
          instrument: signal.instrument,
          confidence: signal.confidence,
          actioned: true,
          accuracy: signal.confidence // Initial accuracy estimate
        });

        // Record order execution
        this.tradingMetrics.recordOrderExecution({
          orderId: result.orderId,
          instrument: signal.instrument,
          executionTime,
          latency: result.latency || executionTime,
          volume: parseFloat(order.quantity),
          success: result.success !== false
        });

        // Complete flow tracking
        if (flowId) {
          await this.flowRegistryClient.completeFlow(flowId, {
            success: result.success !== false,
            message: result.success !== false ? 'AI trade executed successfully' : result.error,
            data: {
              order,
              result,
              signal
            }
          }, {
            executionTime,
            aiSignalUsed: true,
            confidence: signal.confidence
          });
        }

        res.json({
          success: true,
          data: {
            ...result,
            aiSignal: signal,
            order,
            flowId,
            executionTime: `${executionTime}ms`,
            performance: {
              latency: `${result.latency || executionTime}ms`,
              confidence: `${Math.round(signal.confidence * 100)}%`,
              targetCompliance: (result.latency || executionTime) < 10 ? 'PASSED' : 'WARNING'
            }
          }
        });

      } catch (error) {
        const executionTime = Date.now() - startTime;

        this.tradingMetrics.recordError({
          type: 'ai_trade_execution_error',
          message: error.message
        });

        if (flowId) {
          await this.flowRegistryClient.completeFlow(flowId, {
            success: false,
            message: error.message,
            error: error.message
          });
        }

        this.logger.error('AI trade execution failed', {
          error: error.message,
          signal: req.body.signal,
          executionTime: `${executionTime}ms`,
          flowId
        });

        res.status(500).json({
          success: false,
          error: 'AI trade execution failed',
          message: error.message,
          flowId,
          executionTime: `${executionTime}ms`
        });
      }
    });

    // Get external market data
    this.app.get('/api/market/data/:exchange/:symbol', async (req, res) => {
      try {
        const { exchange, symbol } = req.params;
        let marketData;

        switch (exchange.toLowerCase()) {
          case 'binance':
            marketData = await this.externalAPIManager.getBinanceMarketData(symbol.toUpperCase());
            break;
          case 'coinbase':
            marketData = await this.externalAPIManager.getCoinbaseMarketData(symbol.toUpperCase());
            break;
          default:
            return res.status(400).json({
              success: false,
              error: 'Unsupported exchange. Supported: binance, coinbase'
            });
        }

        res.json({
          success: true,
          data: marketData
        });

      } catch (error) {
        this.logger.error('Market data request failed', {
          error: error.message,
          exchange: req.params.exchange,
          symbol: req.params.symbol
        });

        res.status(500).json({
          success: false,
          error: 'Failed to get market data',
          message: error.message
        });
      }
    });

    // Get comprehensive trading performance metrics
    this.app.get('/api/performance/comprehensive', (req, res) => {
      try {
        const performanceSummary = this.tradingMetrics.getPerformanceSummary();
        const currentMetrics = this.tradingMetrics.getSnapshot();
        const historicalData = this.tradingMetrics.getHistoricalData('minutely');

        res.json({
          success: true,
          data: {
            summary: performanceSummary,
            current: currentMetrics,
            historical: {
              minutely: historicalData.slice(-30), // Last 30 minutes
              dataPoints: historicalData.length
            },
            integrations: {
              aiOrchestrator: this.aiSignalIntegration.getConnectionStatus(),
              configService: this.flowRegistryClient.getConnectionStatus(),
              externalAPIs: this.externalAPIManager.getConnectionStatus()
            },
            metadata: {
              timestamp: new Date().toISOString(),
              reportGenerated: true
            }
          }
        });

      } catch (error) {
        this.logger.error('Performance metrics request failed', {
          error: error.message
        });

        res.status(500).json({
          success: false,
          error: 'Failed to get performance metrics',
          message: error.message
        });
      }
    });

    // Get flow tracking history
    this.app.get('/api/flows/history', async (req, res) => {
      try {
        const { page = 1, limit = 50, status, type } = req.query;
        const userId = req.headers['user-id'];
        const tenantId = req.headers['tenant-id'];

        const flowHistory = await this.flowRegistryClient.getFlowHistory({
          page: parseInt(page),
          limit: parseInt(limit),
          status,
          type,
          userId,
          tenantId
        });

        res.json({
          success: true,
          data: flowHistory
        });

      } catch (error) {
        this.logger.error('Flow history request failed', {
          error: error.message,
          query: req.query
        });

        res.status(500).json({
          success: false,
          error: 'Failed to get flow history',
          message: error.message
        });
      }
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
   * Calculate position size based on signal and risk parameters
   */
  calculatePositionSize(signal, riskParams = {}) {
    const baseSize = riskParams.baseSize || 1000; // Default base size
    const riskFactor = riskParams.riskFactor || 0.02; // 2% risk
    const confidenceMultiplier = signal.confidence || 0.5;

    // Adjust position size based on confidence and risk
    const positionSize = baseSize * riskFactor * confidenceMultiplier;

    // Apply position limits
    const maxPosition = parseFloat(process.env.MAX_POSITION_SIZE) || 10000000;
    return Math.min(positionSize, maxPosition);
  }

  /**
   * Check health of external service
   */
  async checkServiceHealth(serviceName, port) {
    try {
      const response = await axios.get(`http://localhost:${port}/health`, {
        timeout: 2000
      });
      return {
        service: serviceName,
        status: 'healthy',
        responseTime: response.config.timeout,
        data: response.data
      };
    } catch (error) {
      return {
        service: serviceName,
        status: 'unhealthy',
        error: error.message
      };
    }
  }

  /**
   * Update integration status
   */
  updateIntegrationStatus(service, isHealthy) {
    this.integrationStatus[service] = {
      status: isHealthy ? 'healthy' : 'unhealthy',
      lastCheck: Date.now()
    };
  }

  /**
   * Start the trading engine server
   */
  async start() {
    const port = this.port;
    const host = process.env.HOST || '0.0.0.0';
    
    try {
      // Create logs directory
      const fs = require('fs');
      const logsDir = require('path').join(__dirname, '../logs');
      if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
      }

      // Initialize all integration services
      this.logger.info('Initializing Trading Engine integrations...', {
        service: this.serviceName
      });

      // Wait for core integrations to be ready (with timeout)
      try {
        await Promise.race([
          this.waitForCoreServices(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Service check timeout')), 10000))
        ]);
      } catch (error) {
        const errorMessage = error && error.message ? error.message : 'Service check timeout or error';
        this.logger.warn('Core services check completed with timeout', {
          service: this.serviceName,
          message: 'Proceeding with limited integration mode',
          error: errorMessage
        });
      }
      
      // Start server with proper error handling
      await new Promise((resolve, reject) => {
        this.server.listen(port, host, (err) => {
          if (err) {
            reject(err);
            return;
          }

          this.logger.info('Trading Engine Server started', {
            service: this.serviceName,
            port,
            host,
            environment: process.env.NODE_ENV || 'development',
            targetLatency: `${process.env.TARGET_LATENCY || 10}ms`,
            version: this.version,
            capabilities: [
              'high-performance-trading',
              'ai-signal-integration',
              'flow-registry-tracking',
              'real-time-market-data',
              'external-api-integration',
              'islamic-trading-compliance',
              'comprehensive-metrics'
            ],
            integrations: {
              aiOrchestrator: process.env.AI_ORCHESTRATOR_URL,
              configService: process.env.CONFIG_SERVICE_URL,
              databaseService: process.env.DATABASE_SERVICE_URL,
              dragonflyDB: process.env.DRAGONFLY_URL
            },
            features: {
              aiSignalIntegration: process.env.FEATURE_AI_SIGNAL_INTEGRATION === 'true',
              flowRegistryTracking: process.env.FEATURE_FLOW_REGISTRY_TRACKING === 'true',
              realTimeTrading: process.env.FEATURE_REAL_TIME_TRADING === 'true',
              riskManagement: process.env.FEATURE_RISK_MANAGEMENT === 'true'
            },
            services: {
              orderExecutor: 'active',
              correlationAnalyzer: 'active',
              sessionManager: 'active',
              islamicTrading: 'active',
              aiSignalIntegration: this.aiSignalIntegration.isHealthy() ? 'active' : 'initializing',
              flowRegistryClient: this.flowRegistryClient.isHealthy() ? 'active' : 'initializing',
              tradingMetrics: 'active',
              externalAPIManager: this.externalAPIManager.isHealthy() ? 'active' : 'limited'
            }
          });

          resolve();
        });
      });
      
      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());
      
    } catch (error) {
      const errorMessage = error && error.message ? error.message : 'Unknown error occurred';
      const errorStack = error && error.stack ? error.stack : 'No stack trace available';

      this.logger.error('Failed to start Trading Engine Server', {
        service: this.serviceName,
        error: errorMessage,
        stack: errorStack
      });
      process.exit(1);
    }
  }

  /**
   * Wait for core services to be ready
   */
  async waitForCoreServices() {
    const maxRetries = 3;
    const retryInterval = 1000; // 1 second

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        this.logger.info(`Core services health check (attempt ${attempt}/${maxRetries})`, {
          service: this.serviceName
        });

        // Check critical services
        const serviceChecks = await Promise.allSettled([
          this.checkServiceHealth('ai-orchestrator', process.env.AI_ORCHESTRATOR_PORT),
          this.checkServiceHealth('config-service', process.env.CONFIG_SERVICE_PORT),
          this.checkServiceHealth('database-service', process.env.DATABASE_SERVICE_PORT)
        ]);

        const healthyServices = serviceChecks.filter(check =>
          check.status === 'fulfilled' && check.value.status === 'healthy'
        ).length;

        if (healthyServices >= 2) { // At least 2 out of 3 core services
          this.logger.info('Core services ready', {
            service: this.serviceName,
            healthyServices: `${healthyServices}/3`,
            attempt
          });
          return;
        }

        if (attempt < maxRetries) {
          this.logger.warn('Waiting for core services to be ready...', {
            service: this.serviceName,
            healthyServices: `${healthyServices}/3`,
            nextRetryIn: `${retryInterval/1000}s`
          });
          await new Promise(resolve => setTimeout(resolve, retryInterval));
        }

      } catch (error) {
        this.logger.error('Error checking core services', {
          service: this.serviceName,
          error: error.message,
          attempt
        });

        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryInterval));
        }
      }
    }

    this.logger.warn('Started without all core services ready', {
      service: this.serviceName,
      message: 'Some integrations may be limited until services are available'
    });
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
    const errorMessage = error && error.message ? error.message : 'Unknown error occurred';
    logger.error('Failed to start server', {
      error: errorMessage,
      stack: error && error.stack ? error.stack : 'No stack trace available'
    });
    process.exit(1);
  });
}

module.exports = TradingEngineServer;