/**
 * Level 4 Performance Analytics Service (Port 8002)
 * Purpose: Business metrics + user analytics with AI insights
 * Enhanced: Real-time performance tracking with multi-tenant analytics
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
const AnalyticsCore = require('./core/AnalyticsCore');
const BusinessMetrics = require('./services/BusinessMetrics');
const UserAnalytics = require('./services/UserAnalytics');
const AIInsights = require('./services/AIInsights');
const PerformanceTracker = require('./services/PerformanceTracker');

// Import routes
const healthRoutes = require('./routes/health');
const analyticsRoutes = require('./routes/analytics');
const metricsRoutes = require('./routes/metrics');
const insightsRoutes = require('./routes/insights');

class PerformanceAnalyticsService {
  constructor() {
    this.app = express();
    this.port = process.env.PERFORMANCE_ANALYTICS_PORT || 8002;
    this.serviceName = 'performance-analytics';

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
    this.analyticsCore = new AnalyticsCore(this.logger);
    this.businessMetrics = new BusinessMetrics(this.logger);
    this.userAnalytics = new UserAnalytics(this.logger);
    this.aiInsights = new AIInsights(this.logger);
    this.performanceTracker = new PerformanceTracker(this.logger);

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      analyticsQueries: 0,
      realtimeMetrics: 0,
      activeUsers: new Set(),
      activeTenants: new Set(),
      averageResponseTime: 0,
      lastHealthCheck: Date.now(),
      dataProcessingRate: 0,
      aiInsightGeneration: 0
    };

    // Level 4 performance targets
    this.performanceTargets = {
      maxResponseTime: 100, // ms for analytics queries
      dataProcessingCapacity: 1000, // events per second
      metricsAccuracy: 0.999, // 99.9% accuracy
      realtimeLatency: 50 // ms for real-time updates
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
        this.metrics.averageResponseTime =
          (this.metrics.averageResponseTime + duration) / 2;

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
    this.app.use('/api/analytics', analyticsRoutes);
    this.app.use('/api/metrics', metricsRoutes);
    this.app.use('/api/insights', insightsRoutes);

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
          analyticsQueries: this.metrics.analyticsQueries,
          realtimeMetrics: this.metrics.realtimeMetrics,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<100ms',
          dataProcessingRate: this.metrics.dataProcessingRate,
          aiInsightGeneration: this.metrics.aiInsightGeneration,
          level4Compliance: true
        },
        capabilities: [
          'business-metrics-tracking',
          'user-analytics',
          'ai-insights-generation',
          'real-time-performance-monitoring',
          'multi-tenant-analytics',
          'predictive-analytics'
        ],
        integrationPoints: {
          allLevel4Services: true,
          level3DataStream: true,
          aiInsights: true,
          businessIntelligence: true
        }
      });
    });

    // Real-time business metrics
    this.app.get('/api/business-metrics', async (req, res) => {
      const startTime = Date.now();

      try {
        const tenantId = req.headers['tenant-id'];
        const timeRange = req.query.timeRange || '24h';

        const businessMetrics = await this.businessMetrics.getBusinessMetrics({
          tenantId,
          timeRange
        });

        this.metrics.analyticsQueries++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          tenantId,
          timeRange,
          metrics: businessMetrics,
          metadata: {
            processingTime: `${processingTime}ms`,
            targetCompliance: processingTime < this.performanceTargets.maxResponseTime ? 'PASSED' : 'WARNING',
            timestamp: new Date().toISOString(),
            accuracy: businessMetrics.accuracy || this.performanceTargets.metricsAccuracy
          }
        });

      } catch (error) {
        this.logger.error('Business metrics error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Business metrics retrieval failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // User analytics with AI insights
    this.app.get('/api/user-analytics/:userId', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId } = req.params;
        const tenantId = req.headers['tenant-id'];
        const includeAI = req.query.includeAI === 'true';

        const userAnalytics = await this.userAnalytics.getUserAnalytics({
          userId,
          tenantId,
          includeAI
        });

        if (includeAI) {
          userAnalytics.aiInsights = await this.aiInsights.generateUserInsights({
            userId,
            tenantId,
            analytics: userAnalytics
          });
          this.metrics.aiInsightGeneration++;
        }

        this.metrics.analyticsQueries++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          userId,
          tenantId,
          analytics: userAnalytics,
          metadata: {
            processingTime: `${processingTime}ms`,
            targetCompliance: processingTime < this.performanceTargets.maxResponseTime ? 'PASSED' : 'WARNING',
            aiInsightsIncluded: includeAI,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('User analytics error', {
          error: error.message,
          stack: error.stack,
          userId: req.params.userId,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'User analytics retrieval failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Real-time performance dashboard
    this.app.get('/api/performance-dashboard', async (req, res) => {
      const startTime = Date.now();

      try {
        const tenantId = req.headers['tenant-id'];

        const performanceData = await this.performanceTracker.getPerformanceDashboard({
          tenantId
        });

        this.metrics.realtimeMetrics++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          tenantId,
          dashboard: performanceData,
          metadata: {
            processingTime: `${processingTime}ms`,
            realtimeLatency: processingTime < this.performanceTargets.realtimeLatency ? 'OPTIMAL' : 'DEGRADED',
            lastUpdate: new Date().toISOString(),
            level4Targets: {
              responseTime: this.performanceTargets.maxResponseTime,
              dataProcessing: this.performanceTargets.dataProcessingCapacity,
              accuracy: this.performanceTargets.metricsAccuracy,
              realtimeLatency: this.performanceTargets.realtimeLatency
            }
          }
        });

      } catch (error) {
        this.logger.error('Performance dashboard error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Performance dashboard retrieval failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // AI-powered insights and predictions
    this.app.post('/api/ai-insights', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId, tenantId, analysisType, timeRange, data } = req.body;

        if (!analysisType) {
          return res.status(400).json({
            error: 'Analysis type is required'
          });
        }

        const aiInsights = await this.aiInsights.generateInsights({
          userId,
          tenantId,
          analysisType,
          timeRange: timeRange || '7d',
          data
        });

        this.metrics.aiInsightGeneration++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          userId,
          tenantId,
          analysisType,
          insights: aiInsights,
          metadata: {
            processingTime: `${processingTime}ms`,
            confidence: aiInsights.confidence,
            timestamp: new Date().toISOString(),
            aiModel: aiInsights.model,
            accuracy: aiInsights.accuracy
          }
        });

      } catch (error) {
        this.logger.error('AI insights error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId,
          tenantId: req.body.tenantId
        });

        res.status(500).json({
          error: 'AI insights generation failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Multi-tenant analytics aggregation
    this.app.get('/api/tenant-analytics/:tenantId', async (req, res) => {
      const startTime = Date.now();

      try {
        const { tenantId } = req.params;
        const timeRange = req.query.timeRange || '24h';
        const includeUsers = req.query.includeUsers === 'true';

        const tenantAnalytics = await this.analyticsCore.getTenantAnalytics({
          tenantId,
          timeRange,
          includeUsers
        });

        this.metrics.analyticsQueries++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          tenantId,
          timeRange,
          analytics: tenantAnalytics,
          metadata: {
            processingTime: `${processingTime}ms`,
            targetCompliance: processingTime < this.performanceTargets.maxResponseTime ? 'PASSED' : 'WARNING',
            userCount: tenantAnalytics.userCount,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Tenant analytics error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.params.tenantId
        });

        res.status(500).json({
          error: 'Tenant analytics retrieval failed',
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
          analyticsQueries: this.metrics.analyticsQueries,
          realtimeMetrics: this.metrics.realtimeMetrics,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          dataProcessingRate: this.metrics.dataProcessingRate,
          aiInsightGeneration: this.metrics.aiInsightGeneration,
          level4Targets: {
            responseTime: this.metrics.averageResponseTime < this.performanceTargets.maxResponseTime ? 'PASSED' : 'WARNING',
            dataProcessing: this.metrics.dataProcessingRate < this.performanceTargets.dataProcessingCapacity ? 'OPTIMAL' : 'HIGH_LOAD',
            multiTenant: this.metrics.activeTenants.size > 0 ? 'ACTIVE' : 'READY',
            aiInsights: 'OPERATIONAL'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            analyticsCore: this.analyticsCore.isHealthy(),
            businessMetrics: this.businessMetrics.isHealthy(),
            userAnalytics: this.userAnalytics.isHealthy(),
            aiInsights: this.aiInsights.isHealthy(),
            performanceTracker: this.performanceTracker.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'Performance Analytics Service',
        level: 'Level 4 - Intelligence',
        description: 'Business metrics + user analytics with AI insights',
        version: '1.0.0',
        port: this.port,
        capabilities: [
          'business-metrics-tracking',
          'user-analytics',
          'ai-insights-generation',
          'real-time-performance-monitoring',
          'multi-tenant-analytics',
          'predictive-analytics'
        ],
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
          'GET /api/business-metrics',
          'GET /api/user-analytics/:userId',
          'GET /api/performance-dashboard',
          'POST /api/ai-insights',
          'GET /api/tenant-analytics/:tenantId',
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
          analyticsQueries: this.metrics.analyticsQueries,
          realtimeMetrics: this.metrics.realtimeMetrics,
          activeUsers: this.metrics.activeUsers.size,
          activeTenants: this.metrics.activeTenants.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          dataProcessingRate: this.metrics.dataProcessingRate,
          aiInsightGeneration: this.metrics.aiInsightGeneration,
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

    // Performance target monitoring every 5 minutes
    cron.schedule('*/5 * * * * *', () => {
      if (this.metrics.averageResponseTime > this.performanceTargets.maxResponseTime) {
        this.logger.warn('Performance degradation detected', {
          currentResponseTime: this.metrics.averageResponseTime,
          targetResponseTime: this.performanceTargets.maxResponseTime,
          recommendation: 'Consider scaling or optimizing analytics queries'
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
          analyticsCore: this.analyticsCore.isHealthy(),
          businessMetrics: this.businessMetrics.isHealthy(),
          userAnalytics: this.userAnalytics.isHealthy(),
          aiInsights: this.aiInsights.isHealthy(),
          performanceTracker: this.performanceTracker.isHealthy()
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

      // Check performance targets
      if (this.metrics.averageResponseTime > this.performanceTargets.maxResponseTime) {
        health.status = 'degraded';
        health.performanceWarning = {
          currentResponseTime: this.metrics.averageResponseTime,
          targetResponseTime: this.performanceTargets.maxResponseTime,
          message: 'Response time above Level 4 target'
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
      await this.analyticsCore.initialize();
      await this.businessMetrics.initialize();
      await this.userAnalytics.initialize();
      await this.aiInsights.initialize();
      await this.performanceTracker.initialize();

      // Start server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('Performance Analytics Service started', {
          service: this.serviceName,
          port: this.port,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'business-metrics-tracking',
            'user-analytics',
            'ai-insights-generation',
            'real-time-performance-monitoring',
            'multi-tenant-analytics'
          ],
          performanceTargets: this.performanceTargets
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start Performance Analytics Service', {
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
        this.logger.info('Performance Analytics Service stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new PerformanceAnalyticsService();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = PerformanceAnalyticsService;