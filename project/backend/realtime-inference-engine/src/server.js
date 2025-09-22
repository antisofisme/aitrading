/**
 * Level 4 Real-time Inference Engine (Port 8017)
 * Purpose: <15ms decision making with multi-tenant AI coordination
 * Integrates: Level 3 data stream + Level 4 AI services for real-time inference
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');
const { WebSocketServer } = require('ws');

// Load environment variables
dotenv.config();

// Import core modules
const InferenceCore = require('./core/InferenceCore');
const DataStreamIntegrator = require('./services/DataStreamIntegrator');
const AIServiceOrchestrator = require('./services/AIServiceOrchestrator');
const DecisionEngine = require('./services/DecisionEngine');
const PerformanceOptimizer = require('./services/PerformanceOptimizer');

// Import routes
const healthRoutes = require('./routes/health');
const inferenceRoutes = require('./routes/inference');
const decisionRoutes = require('./routes/decisions');
const streamRoutes = require('./routes/stream');

class RealtimeInferenceEngine {
  constructor() {
    this.app = express();
    this.port = process.env.INFERENCE_ENGINE_PORT || 8017;
    this.serviceName = 'realtime-inference-engine';

    // Initialize logger
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: {
        service: this.serviceName,
        level: 'level4-intelligence'
      },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}-error.log`,
          level: 'error'
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}.log`
        })
      ]
    });

    // Initialize core components
    this.inferenceCore = new InferenceCore(this.logger);
    this.dataStreamIntegrator = new DataStreamIntegrator(this.logger);
    this.aiServiceOrchestrator = new AIServiceOrchestrator(this.logger);
    this.decisionEngine = new DecisionEngine(this.logger);
    this.performanceOptimizer = new PerformanceOptimizer(this.logger);

    // WebSocket for real-time streaming
    this.wsClients = new Map(); // User-specific WebSocket connections

    // Performance tracking (Level 4 requirement: <15ms)
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      inferenceCount: 0,
      decisionCount: 0,
      activeUsers: new Set(),
      activeTenants: new Set(),
      averageInferenceTime: 0,
      averageDecisionTime: 0,
      lastHealthCheck: Date.now(),
      dataStreamRate: 0,
      errorRate: 0,
      successfulDecisions: 0
    };

    // Level 4 performance targets
    this.performanceTargets = {
      maxInferenceTime: 15, // ms - Level 4 requirement
      maxDecisionTime: 10, // ms for decision making
      minDataStreamRate: 50, // TPS from Level 3
      maxErrorRate: 0.001, // 0.1% error rate
      minAccuracy: 0.65 // >65% AI accuracy
    };

    this.initializeMiddleware();
    this.initializeRoutes();
    this.initializeWebSocket();
    this.initializeErrorHandling();
    this.setupPerformanceMonitoring();
  }

  initializeMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging and metrics
    this.app.use((req, res, next) => {
      const startTime = Date.now();

      // Track multi-tenant usage
      if (req.headers['user-id']) {
        this.metrics.activeUsers.add(req.headers['user-id']);
      }
      if (req.headers['tenant-id']) {
        this.metrics.activeTenants.add(req.headers['tenant-id']);
      }

      // Request logging
      this.logger.info('Incoming request', {
        method: req.method,
        url: req.url,
        userAgent: req.get('User-Agent'),
        userId: req.headers['user-id'],
        tenantId: req.headers['tenant-id'],
        ip: req.ip
      });

      // Response time tracking
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        this.metrics.requestCount++;

        this.logger.info('Request completed', {
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          userId: req.headers['user-id'],
          tenantId: req.headers['tenant-id']
        });
      });

      next();
    });
  }

  initializeRoutes() {
    // API routes
    this.app.use('/health', healthRoutes);
    this.app.use('/api/inference', inferenceRoutes);
    this.app.use('/api/decisions', decisionRoutes);
    this.app.use('/api/stream', streamRoutes);

    // Level 4 specific endpoints
    this.app.get('/api/status', (req, res) => {
      res.json({
        service: this.serviceName,
        level: 'level4-intelligence',
        status: 'operational',
        version: '1.0.0',
        uptime: Date.now() - this.metrics.startTime,
        performance: {
          requestCount: this.metrics.requestCount,
          inferenceCount: this.metrics.inferenceCount,
          decisionCount: this.metrics.decisionCount,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageInferenceTime: Math.round(this.metrics.averageInferenceTime),
          averageDecisionTime: Math.round(this.metrics.averageDecisionTime),
          targetInferenceTime: '<15ms',
          dataStreamRate: this.metrics.dataStreamRate,
          errorRate: Math.round(this.metrics.errorRate * 10000) / 100, // percentage
          successfulDecisions: this.metrics.successfulDecisions,
          level4Compliance: this.metrics.averageInferenceTime < this.performanceTargets.maxInferenceTime
        },
        capabilities: [
          'real-time-ai-inference',
          'multi-tenant-decision-making',
          'level3-data-stream-integration',
          'sub-15ms-processing',
          'ai-service-orchestration',
          'performance-optimization'
        ],
        integrationPoints: {
          level3DataStream: true,
          featureEngineering: true,
          mlAutoML: true,
          performanceAnalytics: true,
          configurationService: true
        }
      });
    });

    // Real-time inference endpoint
    this.app.post('/api/real-time-inference', async (req, res) => {
      const startTime = Date.now();

      try {
        const {
          userId,
          tenantId,
          symbol,
          marketData,
          inferenceType,
          modelPreferences
        } = req.body;

        if (!userId || !symbol || !marketData) {
          return res.status(400).json({
            error: 'Missing required fields: userId, symbol, marketData'
          });
        }

        // Execute real-time inference with performance optimization
        const inferenceResult = await this.inferenceCore.executeRealTimeInference({
          userId,
          tenantId,
          symbol,
          marketData,
          inferenceType: inferenceType || 'trading_decision',
          modelPreferences,
          startTime
        });

        this.metrics.inferenceCount++;
        const inferenceTime = Date.now() - startTime;
        this.metrics.averageInferenceTime =
          (this.metrics.averageInferenceTime + inferenceTime) / 2;

        // Stream result to WebSocket clients if connected
        this.streamToUser(userId, {
          type: 'inference_result',
          result: inferenceResult,
          inferenceTime
        });

        res.json({
          success: true,
          userId,
          tenantId,
          symbol,
          inference: inferenceResult,
          metadata: {
            inferenceTime: `${inferenceTime}ms`,
            targetCompliance: inferenceTime < this.performanceTargets.maxInferenceTime ? 'PASSED' : 'WARNING',
            accuracy: inferenceResult.accuracy,
            confidence: inferenceResult.confidence,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.metrics.errorRate = (this.metrics.errorRate + 1) / 2;
        this.logger.error('Real-time inference error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId,
          tenantId: req.body.tenantId
        });

        res.status(500).json({
          error: 'Real-time inference failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // AI decision making endpoint
    this.app.post('/api/make-decision', async (req, res) => {
      const startTime = Date.now();

      try {
        const {
          userId,
          tenantId,
          context,
          options,
          constraints
        } = req.body;

        if (!userId || !context) {
          return res.status(400).json({
            error: 'Missing required fields: userId, context'
          });
        }

        // Execute AI decision making
        const decision = await this.decisionEngine.makeDecision({
          userId,
          tenantId,
          context,
          options: options || [],
          constraints: constraints || {},
          startTime
        });

        this.metrics.decisionCount++;
        const decisionTime = Date.now() - startTime;
        this.metrics.averageDecisionTime =
          (this.metrics.averageDecisionTime + decisionTime) / 2;

        if (decision.success) {
          this.metrics.successfulDecisions++;
        }

        // Stream decision to WebSocket clients
        this.streamToUser(userId, {
          type: 'decision_result',
          decision,
          decisionTime
        });

        res.json({
          success: decision.success,
          userId,
          tenantId,
          decision: decision.result,
          rationale: decision.rationale,
          metadata: {
            decisionTime: `${decisionTime}ms`,
            targetCompliance: decisionTime < this.performanceTargets.maxDecisionTime ? 'PASSED' : 'WARNING',
            confidence: decision.confidence,
            accuracy: decision.accuracy,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.metrics.errorRate = (this.metrics.errorRate + 1) / 2;
        this.logger.error('Decision making error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId,
          tenantId: req.body.tenantId
        });

        res.status(500).json({
          error: 'Decision making failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Level 3 data stream integration status
    this.app.get('/api/data-stream-status', async (req, res) => {
      try {
        const streamStatus = await this.dataStreamIntegrator.getStreamStatus();

        res.json({
          success: true,
          dataStream: streamStatus,
          level3Integration: {
            connected: streamStatus.connected,
            ticksPerSecond: streamStatus.ticksPerSecond,
            targetTPS: this.performanceTargets.minDataStreamRate,
            compliance: streamStatus.ticksPerSecond >= this.performanceTargets.minDataStreamRate ? 'PASSED' : 'WARNING',
            latency: streamStatus.latency,
            lastUpdate: streamStatus.lastUpdate
          },
          metadata: {
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Data stream status error', {
          error: error.message,
          stack: error.stack
        });

        res.status(500).json({
          error: 'Failed to get data stream status',
          message: error.message
        });
      }
    });

    // AI service orchestration status
    this.app.get('/api/ai-services-status', async (req, res) => {
      try {
        const servicesStatus = await this.aiServiceOrchestrator.getServicesStatus();

        res.json({
          success: true,
          aiServices: servicesStatus,
          level4Integration: {
            featureEngineering: servicesStatus.featureEngineering,
            mlAutoML: servicesStatus.mlAutoML,
            performanceAnalytics: servicesStatus.performanceAnalytics,
            configurationService: servicesStatus.configurationService,
            allServicesHealthy: servicesStatus.allHealthy,
            averageResponseTime: servicesStatus.averageResponseTime
          },
          metadata: {
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('AI services status error', {
          error: error.message,
          stack: error.stack
        });

        res.status(500).json({
          error: 'Failed to get AI services status',
          message: error.message
        });
      }
    });

    // Performance optimization endpoint
    this.app.post('/api/optimize-performance', async (req, res) => {
      try {
        const { userId, optimizationType } = req.body;

        const optimization = await this.performanceOptimizer.optimizeForUser({
          userId,
          type: optimizationType || 'inference_speed',
          currentMetrics: {
            averageInferenceTime: this.metrics.averageInferenceTime,
            averageDecisionTime: this.metrics.averageDecisionTime,
            errorRate: this.metrics.errorRate
          }
        });

        res.json({
          success: true,
          userId,
          optimization,
          metadata: {
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Performance optimization error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Performance optimization failed',
          message: error.message
        });
      }
    });

    // Performance metrics endpoint
    this.app.get('/api/performance', (req, res) => {
      const uptime = Date.now() - this.metrics.startTime;

      res.json({
        service: this.serviceName,
        performance: {
          uptime: `${Math.floor(uptime / 1000)}s`,
          requestCount: this.metrics.requestCount,
          inferenceCount: this.metrics.inferenceCount,
          decisionCount: this.metrics.decisionCount,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageInferenceTime: Math.round(this.metrics.averageInferenceTime),
          averageDecisionTime: Math.round(this.metrics.averageDecisionTime),
          dataStreamRate: this.metrics.dataStreamRate,
          errorRate: Math.round(this.metrics.errorRate * 10000) / 100,
          successfulDecisions: this.metrics.successfulDecisions,
          level4Targets: {
            inferenceTime: this.metrics.averageInferenceTime < this.performanceTargets.maxInferenceTime ? 'PASSED' : 'WARNING',
            decisionTime: this.metrics.averageDecisionTime < this.performanceTargets.maxDecisionTime ? 'PASSED' : 'WARNING',
            dataStreamRate: this.metrics.dataStreamRate >= this.performanceTargets.minDataStreamRate ? 'PASSED' : 'WARNING',
            errorRate: this.metrics.errorRate < this.performanceTargets.maxErrorRate ? 'PASSED' : 'WARNING',
            multiTenant: this.metrics.activeTenants.size > 0 ? 'ACTIVE' : 'READY'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            inferenceCore: this.inferenceCore.isHealthy(),
            dataStreamIntegrator: this.dataStreamIntegrator.isHealthy(),
            aiServiceOrchestrator: this.aiServiceOrchestrator.isHealthy(),
            decisionEngine: this.decisionEngine.isHealthy(),
            performanceOptimizer: this.performanceOptimizer.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'Real-time Inference Engine',
        level: 'Level 4 - Intelligence',
        description: '<15ms decision making with multi-tenant AI coordination',
        version: '1.0.0',
        port: this.port,
        capabilities: [
          'real-time-ai-inference',
          'multi-tenant-decision-making',
          'level3-data-stream-integration',
          'sub-15ms-processing',
          'ai-service-orchestration',
          'performance-optimization'
        ],
        documentation: '/api/docs',
        health: '/health',
        status: '/api/status'
      });
    });
  }

  initializeWebSocket() {
    this.wss = new WebSocketServer({
      port: this.port + 1000, // WebSocket on port 9017
      path: '/ws'
    });

    this.wss.on('connection', (ws, req) => {
      const userId = req.url.split('userId=')[1]?.split('&')[0];

      if (userId) {
        if (!this.wsClients.has(userId)) {
          this.wsClients.set(userId, new Set());
        }
        this.wsClients.get(userId).add(ws);

        this.logger.info('WebSocket client connected', {
          userId,
          totalConnections: Array.from(this.wsClients.values())
            .reduce((total, userConnections) => total + userConnections.size, 0)
        });

        ws.on('close', () => {
          if (this.wsClients.has(userId)) {
            this.wsClients.get(userId).delete(ws);
            if (this.wsClients.get(userId).size === 0) {
              this.wsClients.delete(userId);
            }
          }
          this.logger.info('WebSocket client disconnected', { userId });
        });

        ws.on('error', (error) => {
          this.logger.error('WebSocket error', {
            error: error.message,
            userId
          });
          if (this.wsClients.has(userId)) {
            this.wsClients.get(userId).delete(ws);
          }
        });

        // Send initial connection confirmation
        ws.send(JSON.stringify({
          type: 'connection',
          message: 'Connected to Real-time Inference Engine',
          userId,
          timestamp: new Date().toISOString()
        }));
      } else {
        ws.close(1000, 'User ID required');
      }
    });
  }

  streamToUser(userId, data) {
    if (this.wsClients.has(userId)) {
      const userConnections = this.wsClients.get(userId);
      let successCount = 0;

      userConnections.forEach(client => {
        try {
          if (client.readyState === 1) { // WebSocket.OPEN
            client.send(JSON.stringify(data));
            successCount++;
          }
        } catch (error) {
          this.logger.error('Failed to send WebSocket message', {
            error: error.message,
            userId
          });
          userConnections.delete(client);
        }
      });

      this.logger.debug('Streamed data to user', {
        userId,
        clientsNotified: successCount,
        totalClients: userConnections.size,
        dataType: data.type
      });
    }
  }

  initializeErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        service: this.serviceName,
        availableEndpoints: [
          'GET /health',
          'GET /api/status',
          'POST /api/real-time-inference',
          'POST /api/make-decision',
          'GET /api/data-stream-status',
          'GET /api/ai-services-status',
          'POST /api/optimize-performance',
          'GET /api/performance'
        ]
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      this.logger.error('Unhandled error', {
        error: error.message,
        stack: error.stack,
        url: req.url,
        method: req.method,
        userId: req.headers['user-id'],
        tenantId: req.headers['tenant-id']
      });

      res.status(500).json({
        error: 'Internal server error',
        message: error.message,
        service: this.serviceName,
        timestamp: new Date().toISOString()
      });
    });
  }

  setupPerformanceMonitoring() {
    // Health check every 30 seconds
    cron.schedule('*/30 * * * * *', () => {
      this.metrics.lastHealthCheck = Date.now();
      this.performHealthCheck();
    });

    // Performance metrics logging every minute
    cron.schedule('0 * * * * *', () => {
      this.logger.info('Performance metrics', {
        service: this.serviceName,
        metrics: {
          uptime: Date.now() - this.metrics.startTime,
          requestCount: this.metrics.requestCount,
          inferenceCount: this.metrics.inferenceCount,
          decisionCount: this.metrics.decisionCount,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageInferenceTime: Math.round(this.metrics.averageInferenceTime),
          averageDecisionTime: Math.round(this.metrics.averageDecisionTime),
          dataStreamRate: this.metrics.dataStreamRate,
          errorRate: Math.round(this.metrics.errorRate * 10000) / 100,
          successfulDecisions: this.metrics.successfulDecisions,
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Reset user and tenant sessions every hour
    cron.schedule('0 0 * * * *', () => {
      this.metrics.activeUsers.clear();
      this.metrics.activeTenants.clear();
      this.logger.info('User and tenant sessions reset for new hour');
    });

    // Level 4 performance target monitoring every 5 minutes
    cron.schedule('*/5 * * * * *', () => {
      if (this.metrics.averageInferenceTime > this.performanceTargets.maxInferenceTime) {
        this.logger.warn('Inference time exceeds Level 4 target', {
          currentInferenceTime: this.metrics.averageInferenceTime,
          targetInferenceTime: this.performanceTargets.maxInferenceTime,
          recommendation: 'Consider performance optimization or scaling'
        });
      }

      if (this.metrics.dataStreamRate < this.performanceTargets.minDataStreamRate) {
        this.logger.warn('Data stream rate below Level 3 output', {
          currentDataStreamRate: this.metrics.dataStreamRate,
          targetDataStreamRate: this.performanceTargets.minDataStreamRate,
          recommendation: 'Check Level 3 data stream connection'
        });
      }
    });

    // Update data stream rate every 10 seconds
    cron.schedule('*/10 * * * * *', async () => {
      try {
        const streamStatus = await this.dataStreamIntegrator.getStreamStatus();
        this.metrics.dataStreamRate = streamStatus.ticksPerSecond || 0;
      } catch (error) {
        this.logger.error('Failed to update data stream rate', {
          error: error.message
        });
      }
    });
  }

  async performHealthCheck() {
    try {
      const health = {
        service: this.serviceName,
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: Date.now() - this.metrics.startTime,
        components: {
          inferenceCore: this.inferenceCore.isHealthy(),
          dataStreamIntegrator: this.dataStreamIntegrator.isHealthy(),
          aiServiceOrchestrator: this.aiServiceOrchestrator.isHealthy(),
          decisionEngine: this.decisionEngine.isHealthy(),
          performanceOptimizer: this.performanceOptimizer.isHealthy()
        }
      };

      // Check if any components are unhealthy
      const unhealthyComponents = Object.entries(health.components)
        .filter(([, status]) => !status);

      if (unhealthyComponents.length > 0) {
        health.status = 'unhealthy';
        health.issues = unhealthyComponents.map(([component]) => component);
        this.logger.warn('Health check failed', health);
      }

      // Check Level 4 performance targets
      if (this.metrics.averageInferenceTime > this.performanceTargets.maxInferenceTime) {
        health.status = 'degraded';
        health.performanceWarning = {
          issue: 'inference_time_exceeded',
          current: this.metrics.averageInferenceTime,
          target: this.performanceTargets.maxInferenceTime,
          message: 'Inference time exceeds Level 4 requirement'
        };
      }

      if (this.metrics.errorRate > this.performanceTargets.maxErrorRate) {
        health.status = 'degraded';
        health.errorWarning = {
          issue: 'error_rate_exceeded',
          current: this.metrics.errorRate,
          target: this.performanceTargets.maxErrorRate,
          message: 'Error rate exceeds acceptable threshold'
        };
      }

    } catch (error) {
      this.logger.error('Health check error', {
        error: error.message,
        stack: error.stack
      });
    }
  }

  async start() {
    try {
      // Initialize core components
      await this.inferenceCore.initialize();
      await this.dataStreamIntegrator.initialize();
      await this.aiServiceOrchestrator.initialize();
      await this.decisionEngine.initialize();
      await this.performanceOptimizer.initialize();

      // Start server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('Real-time Inference Engine started', {
          service: this.serviceName,
          port: this.port,
          wsPort: this.port + 1000,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'real-time-ai-inference',
            'multi-tenant-decision-making',
            'level3-data-stream-integration',
            'sub-15ms-processing'
          ],
          performanceTargets: this.performanceTargets
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start Real-time Inference Engine', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    // Close WebSocket connections
    this.wsClients.forEach((userConnections, userId) => {
      userConnections.forEach(client => {
        try {
          client.close();
        } catch (error) {
          this.logger.error('Error closing WebSocket client', {
            error: error.message,
            userId
          });
        }
      });
    });

    if (this.wss) {
      this.wss.close();
    }

    if (this.server) {
      this.server.close(() => {
        this.logger.info('Real-time Inference Engine stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new RealtimeInferenceEngine();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = RealtimeInferenceEngine;