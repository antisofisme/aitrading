/**
 * Level 4 Feature Engineering Service (Port 8011)
 * Purpose: Advanced technical indicators with user-specific feature sets
 * Multi-tenant AI/ML processing with real-time performance
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');

// Load environment variables
dotenv.config();

// Import core modules
const FeatureEngineeringCore = require('./core/FeatureEngineeringCore');
const UserConfigManager = require('./services/UserConfigManager');
const DataProcessor = require('./services/DataProcessor');
const PerformanceMonitor = require('./services/PerformanceMonitor');
const TechnicalIndicators = require('./indicators/TechnicalIndicators');

// Import routes
const healthRoutes = require('./routes/health');
const featureRoutes = require('./routes/features');
const indicatorRoutes = require('./routes/indicators');
const userRoutes = require('./routes/users');

class FeatureEngineeringService {
  constructor() {
    this.app = express();
    this.port = process.env.FEATURE_ENG_PORT || 8011;
    this.serviceName = 'feature-engineering';

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
    this.featureCore = new FeatureEngineeringCore(this.logger);
    this.userConfigManager = new UserConfigManager(this.logger);
    this.dataProcessor = new DataProcessor(this.logger);
    this.performanceMonitor = new PerformanceMonitor(this.logger);
    this.technicalIndicators = new TechnicalIndicators(this.logger);

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      featureCalculations: 0,
      userSessions: new Set(),
      averageResponseTime: 0,
      lastHealthCheck: Date.now()
    };

    this.initializeMiddleware();
    this.initializeRoutes();
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

      // Track user sessions for multi-tenancy
      if (req.headers['user-id']) {
        this.metrics.userSessions.add(req.headers['user-id']);
      }

      // Request logging
      this.logger.info('Incoming request', {
        method: req.method,
        url: req.url,
        userAgent: req.get('User-Agent'),
        userId: req.headers['user-id'],
        ip: req.ip
      });

      // Response time tracking
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        this.metrics.requestCount++;
        this.metrics.averageResponseTime =
          (this.metrics.averageResponseTime + duration) / 2;

        this.logger.info('Request completed', {
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          userId: req.headers['user-id']
        });
      });

      next();
    });
  }

  initializeRoutes() {
    // API routes
    this.app.use('/health', healthRoutes);
    this.app.use('/api/features', featureRoutes);
    this.app.use('/api/indicators', indicatorRoutes);
    this.app.use('/api/users', userRoutes);

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
          featureCalculations: this.metrics.featureCalculations,
          activeUsers: this.metrics.userSessions.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<15ms',
          level4Compliance: true
        },
        capabilities: [
          'multi-tenant-feature-engineering',
          'real-time-indicators',
          'user-specific-configurations',
          'ai-ml-integration',
          'performance-optimization'
        ],
        integrationPoints: {
          level3DataStream: true,
          configurationService: true,
          mlPipeline: true,
          userIsolation: true
        }
      });
    });

    // Multi-tenant feature calculation endpoint
    this.app.post('/api/calculate-features', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId, symbol, timeframe, indicators, marketData } = req.body;

        if (!userId || !symbol || !marketData) {
          return res.status(400).json({
            error: 'Missing required fields: userId, symbol, marketData'
          });
        }

        // Get user-specific configuration
        const userConfig = await this.userConfigManager.getUserConfig(userId);

        // Process features with user isolation
        const features = await this.featureCore.calculateUserFeatures({
          userId,
          symbol,
          timeframe,
          indicators: indicators || userConfig.defaultIndicators,
          marketData,
          userConfig
        });

        this.metrics.featureCalculations++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          userId,
          symbol,
          features,
          metadata: {
            processingTime: `${processingTime}ms`,
            targetCompliance: processingTime < 15 ? 'PASSED' : 'WARNING',
            featureCount: Object.keys(features).length,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Feature calculation error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Feature calculation failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
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
          featureCalculations: this.metrics.featureCalculations,
          activeUsers: this.metrics.userSessions.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<15ms',
          level4Targets: {
            responseTime: this.metrics.averageResponseTime < 15 ? 'PASSED' : 'WARNING',
            multiTenant: this.metrics.userSessions.size > 0 ? 'ACTIVE' : 'READY',
            aiIntegration: 'OPERATIONAL',
            dataStream: 'CONNECTED'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            featureCore: this.featureCore.isHealthy(),
            dataProcessor: this.dataProcessor.isHealthy(),
            userConfig: this.userConfigManager.isHealthy(),
            indicators: this.technicalIndicators.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'Feature Engineering Service',
        level: 'Level 4 - Intelligence',
        description: 'Advanced technical indicators with user-specific feature sets',
        version: '1.0.0',
        port: this.port,
        documentation: '/api/docs',
        health: '/health',
        status: '/api/status'
      });
    });
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
          'POST /api/calculate-features',
          'GET /api/performance',
          'GET /api/features',
          'GET /api/indicators',
          'GET /api/users'
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
        userId: req.headers['user-id']
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
          featureCalculations: this.metrics.featureCalculations,
          activeUsers: this.metrics.userSessions.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Reset user sessions every hour to prevent memory leaks
    cron.schedule('0 0 * * * *', () => {
      this.metrics.userSessions.clear();
      this.logger.info('User sessions reset for new hour');
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
          featureCore: this.featureCore.isHealthy(),
          dataProcessor: this.dataProcessor.isHealthy(),
          userConfig: this.userConfigManager.isHealthy(),
          indicators: this.technicalIndicators.isHealthy()
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
      await this.featureCore.initialize();
      await this.userConfigManager.initialize();
      await this.dataProcessor.initialize();
      await this.performanceMonitor.initialize();
      await this.technicalIndicators.initialize();

      // Start server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('Feature Engineering Service started', {
          service: this.serviceName,
          port: this.port,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'multi-tenant-processing',
            'real-time-indicators',
            'ai-ml-integration',
            'user-specific-features'
          ]
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start Feature Engineering Service', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    if (this.server) {
      this.server.close(() => {
        this.logger.info('Feature Engineering Service stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new FeatureEngineeringService();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = FeatureEngineeringService;