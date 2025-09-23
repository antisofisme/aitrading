/**
 * Lightweight API Gateway for AI Trading Platform
 * Production-ready routing service with Flow Registry integration
 * Port 3001 - Routes requests to all microservices
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');

// Load environment variables
dotenv.config({ path: '../../.env.plan2' });

// Import middleware
const AuthMiddleware = require('./middleware/auth');
const RateLimitMiddleware = require('./middleware/rateLimit');
const FlowTrackingMiddleware = require('./middleware/flowTracking');
const ErrorHandlerMiddleware = require('./middleware/errorHandler');

// Import routes
const indexRoutes = require('./routes/index');
const serviceRoutes = require('./routes/services');

class LightweightApiGateway {
  constructor() {
    this.app = express();
    this.port = process.env.API_GATEWAY_PORT || 3001;
    this.serviceName = 'lightweight-api-gateway';

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
        version: '1.0.0'
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

    // Initialize middleware instances
    this.authMiddleware = new AuthMiddleware(this.logger);
    this.rateLimitMiddleware = new RateLimitMiddleware(this.logger);
    this.flowTrackingMiddleware = new FlowTrackingMiddleware(this.logger);
    this.errorHandlerMiddleware = new ErrorHandlerMiddleware(this.logger);

    // Store middleware instances in app locals for access by routes
    this.app.locals.authMiddleware = this.authMiddleware;
    this.app.locals.rateLimitMiddleware = this.rateLimitMiddleware;
    this.app.locals.flowTrackingMiddleware = this.flowTrackingMiddleware;
    this.app.locals.errorHandlerMiddleware = this.errorHandlerMiddleware;

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      proxyRequestCount: 0,
      averageResponseTime: 0,
      lastHealthCheck: Date.now(),
      activeConnections: 0,
      errorCount: 0,
      successCount: 0
    };

    this.initializeMiddleware();
    this.initializeRoutes();
    this.initializeErrorHandling();
    this.setupPerformanceMonitoring();

    this.logger.info('Lightweight API Gateway initialized', {
      port: this.port,
      environment: process.env.NODE_ENV || 'development',
      features: [
        'JWT Authentication',
        'DragonflyDB Rate Limiting',
        'Flow Registry Integration',
        'Service Health Monitoring',
        'Error Impact Analysis',
        'Request Compression',
        'Security Headers'
      ]
    });
  }

  /**
   * Initialize middleware stack - optimized order for performance
   */
  initializeMiddleware() {
    // Trust proxy for accurate IP addresses
    this.app.set('trust proxy', true);

    // Security middleware (early in stack)
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
          connectSrc: ["'self'", "ws:", "wss:"]
        }
      },
      hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
      }
    }));

    // CORS configuration with environment-based origins
    this.app.use(cors({
      origin: (origin, callback) => {
        const allowedOrigins = process.env.CORS_ORIGIN?.split(',') || ['*'];

        if (allowedOrigins.includes('*') || !origin || allowedOrigins.includes(origin)) {
          callback(null, true);
        } else {
          callback(new Error('Not allowed by CORS'));
        }
      },
      credentials: true,
      optionsSuccessStatus: 200,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: [
        'Origin',
        'X-Requested-With',
        'Content-Type',
        'Accept',
        'Authorization',
        'X-Flow-Id',
        'X-Request-Id',
        'X-Parent-Flow-Id',
        'X-Flow-Depth',
        'user-id',
        'tenant-id',
        'user-role'
      ]
    }));

    // Compression (before body parsing)
    this.app.use(compression({
      filter: (req, res) => {
        if (req.headers['x-no-compression']) {
          return false;
        }
        return compression.filter(req, res);
      },
      threshold: 1024,
      level: 6 // Balanced compression
    }));

    // Body parsing with size limits
    this.app.use(express.json({
      limit: '10mb',
      verify: (req, res, buf, encoding) => {
        req.rawBody = buf;
      }
    }));
    this.app.use(express.urlencoded({
      extended: true,
      limit: '10mb'
    }));

    // Flow tracking (early for complete request tracing)
    this.app.use(this.flowTrackingMiddleware.trackFlow());

    // Request metrics and enhanced logging
    this.app.use((req, res, next) => {
      const startTime = Date.now();
      this.metrics.requestCount++;
      this.metrics.activeConnections++;

      // Enhanced request logging with security context
      this.logger.info('Request received', {
        method: req.method,
        url: req.url,
        path: req.path,
        query: Object.keys(req.query).length > 0 ? req.query : undefined,
        userAgent: req.get('User-Agent'),
        ip: req.ip,
        flowId: req.flowId,
        requestId: req.requestId,
        userId: req.headers['user-id'],
        tenantId: req.headers['tenant-id'],
        contentLength: req.get('content-length'),
        origin: req.get('origin')
      });

      // Response completion tracking
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        this.metrics.averageResponseTime =
          (this.metrics.averageResponseTime + duration) / 2;
        this.metrics.activeConnections--;

        // Track success/error metrics
        if (res.statusCode >= 400) {
          this.metrics.errorCount++;
        } else {
          this.metrics.successCount++;
        }

        this.logger.info('Request completed', {
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          flowId: req.flowId,
          requestId: req.requestId,
          contentLength: res.get('content-length'),
          userId: req.headers['user-id'],
          tenantId: req.headers['tenant-id'],
          success: res.statusCode < 400
        });
      });

      next();
    });

    // Rate limiting with service-specific strategies
    this.setupRateLimiting();

    // Authentication with flexible configuration
    this.app.use(this.authMiddleware.authenticate({
      required: false,
      skipPaths: [
        '/health',
        '/status',
        '/metrics',
        '/services',
        '/',
        '/api/health-summary'
      ]
    }));
  }

  /**
   * Setup rate limiting strategies for different service types
   */
  setupRateLimiting() {
    // Authentication endpoints - strictest limits
    this.app.use('/api/auth', this.rateLimitMiddleware.auth());

    // Trading endpoints - trading-specific limits
    this.app.use('/api/trading', this.rateLimitMiddleware.trading());
    this.app.use('/api/orders', this.rateLimitMiddleware.trading());
    this.app.use('/api/portfolio', this.rateLimitMiddleware.trading());

    // AI/ML endpoints - resource-intensive limits
    this.app.use('/api/ai', this.rateLimitMiddleware.aiMl());
    this.app.use('/api/ml', this.rateLimitMiddleware.aiMl());

    // General rate limiting and slow down
    this.app.use(this.rateLimitMiddleware.general());
    this.app.use(this.rateLimitMiddleware.slowDown());
  }

  /**
   * Initialize routes
   */
  initializeRoutes() {
    // Gateway-specific routes (health, status, metrics)
    this.app.use('/', indexRoutes);

    // Service proxy routes - must be last to catch all /api/* routes
    this.app.use('/api', serviceRoutes);

    // Track proxy request metrics
    this.app.use('/api/*', (req, res, next) => {
      this.metrics.proxyRequestCount++;
      next();
    });
  }

  /**
   * Initialize error handling
   */
  initializeErrorHandling() {
    // 404 handler for unmatched routes
    this.app.use('*', (req, res) => {
      this.logger.warn('Route not found', {
        method: req.method,
        url: req.url,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        flowId: req.flowId,
        requestId: req.requestId
      });

      res.status(404).json({
        error: 'Route not found',
        message: `${req.method} ${req.url} is not a valid endpoint`,
        code: 'ROUTE_NOT_FOUND',
        suggestion: 'Check /services endpoint for available routes',
        documentation: '/services',
        timestamp: new Date().toISOString(),
        requestId: req.requestId,
        flowId: req.flowId
      });
    });

    // Global error handler
    this.app.use(this.errorHandlerMiddleware.handle());
  }

  /**
   * Setup performance monitoring and maintenance
   */
  setupPerformanceMonitoring() {
    // Health monitoring every 30 seconds
    cron.schedule('*/30 * * * * *', () => {
      this.metrics.lastHealthCheck = Date.now();
      this.performHealthCheck();
    });

    // Performance metrics logging every minute
    cron.schedule('0 * * * * *', () => {
      const uptime = Date.now() - this.metrics.startTime;
      const errorRate = this.metrics.requestCount > 0
        ? (this.metrics.errorCount / this.metrics.requestCount * 100).toFixed(2)
        : 0;

      this.logger.info('Gateway performance metrics', {
        service: this.serviceName,
        metrics: {
          uptime: `${Math.floor(uptime / 1000)}s`,
          requestCount: this.metrics.requestCount,
          proxyRequestCount: this.metrics.proxyRequestCount,
          averageResponseTime: `${Math.round(this.metrics.averageResponseTime)}ms`,
          activeConnections: this.metrics.activeConnections,
          errorRate: `${errorRate}%`,
          successCount: this.metrics.successCount,
          errorCount: this.metrics.errorCount,
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Cache cleanup every 5 minutes
    cron.schedule('*/5 * * * *', async () => {
      try {
        const cleanupResults = await Promise.allSettled([
          this.rateLimitMiddleware.cleanup(),
          this.flowTrackingMiddleware.cleanupCache()
        ]);

        this.logger.info('Periodic cache cleanup completed', {
          rateLimitCleanup: cleanupResults[0].status === 'fulfilled' ? cleanupResults[0].value : 'failed',
          flowTrackingCleanup: cleanupResults[1].status === 'fulfilled' ? cleanupResults[1].value : 'failed'
        });
      } catch (error) {
        this.logger.error('Cache cleanup error', {
          error: error.message
        });
      }
    });

    // Memory optimization every 30 minutes
    cron.schedule('*/30 * * * *', () => {
      if (global.gc) {
        global.gc();
        this.logger.info('Manual garbage collection triggered');
      }
    });

    // Daily metrics reset (keeps long-term stats manageable)
    cron.schedule('0 0 * * *', () => {
      this.metrics.requestCount = 0;
      this.metrics.proxyRequestCount = 0;
      this.metrics.errorCount = 0;
      this.metrics.successCount = 0;
      this.metrics.averageResponseTime = 0;

      this.logger.info('Daily metrics reset completed');
    });
  }

  /**
   * Perform comprehensive health check
   */
  async performHealthCheck() {
    try {
      const memoryUsage = process.memoryUsage();
      const uptime = Date.now() - this.metrics.startTime;

      const health = {
        service: this.serviceName,
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: `${Math.floor(uptime / 1000)}s`,
        version: '1.0.0',
        metrics: {
          requestCount: this.metrics.requestCount,
          proxyRequestCount: this.metrics.proxyRequestCount,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          activeConnections: this.metrics.activeConnections,
          errorRate: this.metrics.requestCount > 0
            ? (this.metrics.errorCount / this.metrics.requestCount * 100).toFixed(2)
            : 0
        },
        memory: {
          heapUsed: `${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`,
          heapTotal: `${Math.round(memoryUsage.heapTotal / 1024 / 1024)}MB`,
          external: `${Math.round(memoryUsage.external / 1024 / 1024)}MB`
        },
        warnings: []
      };

      // Health warnings
      const memoryThreshold = 1024 * 1024 * 1024; // 1GB
      if (memoryUsage.heapUsed > memoryThreshold) {
        health.status = 'warning';
        health.warnings.push('High memory usage detected');
        this.logger.warn('High memory usage detected', { memoryUsage });
      }

      if (this.metrics.activeConnections > 1000) {
        health.status = 'warning';
        health.warnings.push('High connection count');
        this.logger.warn('High connection count', {
          activeConnections: this.metrics.activeConnections
        });
      }

      const errorRate = this.metrics.requestCount > 0
        ? (this.metrics.errorCount / this.metrics.requestCount) * 100
        : 0;

      if (errorRate > 10) {
        health.status = 'warning';
        health.warnings.push('High error rate');
        this.logger.warn('High error rate detected', { errorRate });
      }

    } catch (error) {
      this.logger.error('Health check error', {
        error: error.message,
        stack: error.stack
      });
    }
  }

  /**
   * Start the lightweight gateway
   */
  async start() {
    try {
      // Ensure logs directory exists
      const fs = require('fs');
      if (!fs.existsSync('logs')) {
        fs.mkdirSync('logs', { recursive: true });
      }

      // Start HTTP server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('🚀 Lightweight API Gateway started', {
          service: this.serviceName,
          port: this.port,
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          pid: process.pid,
          features: {
            authentication: true,
            rateLimiting: true,
            flowTracking: process.env.FLOW_TRACKING_ENABLED === 'true',
            chainDebugging: process.env.CHAIN_DEBUG_ENABLED === 'true',
            compression: true,
            cors: true,
            security: true,
            healthMonitoring: true
          },
          configuration: {
            configServiceUrl: process.env.CONFIG_SERVICE_URL || 'http://localhost:8012',
            jwtSecret: !!process.env.JWT_SECRET,
            rateLimitWindow: process.env.RATE_LIMIT_WINDOW_MS || '900000',
            maxRequests: process.env.RATE_LIMIT_MAX_REQUESTS || '100',
            dragonflyHost: process.env.DRAGONFLY_HOST || 'localhost',
            postgresHost: process.env.POSTGRES_HOST || 'localhost'
          },
          endpoints: {
            health: `http://localhost:${this.port}/health`,
            status: `http://localhost:${this.port}/status`,
            metrics: `http://localhost:${this.port}/metrics`,
            services: `http://localhost:${this.port}/services`
          }
        });

        console.log(`🚀 Lightweight API Gateway running on port ${this.port}`);
        console.log(`📋 Environment: ${process.env.NODE_ENV || 'development'}`);
        console.log(`🔒 JWT Auth System: ${!!process.env.JWT_SECRET ? 'Active' : 'Disabled'}`);
        console.log(`🗄️  DragonflyDB Rate Limiting: ${process.env.DRAGONFLY_HOST ? 'Enabled' : 'Memory-based'}`);
        console.log(`📊 Flow Tracking: ${process.env.FLOW_TRACKING_ENABLED === 'true' ? 'Enabled' : 'Disabled'}`);
        console.log(`🏥 Health Check: http://localhost:${this.port}/health`);
        console.log(`📈 Metrics: http://localhost:${this.port}/metrics`);
        console.log(`🔧 Services: http://localhost:${this.port}/services`);
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

      // Handle uncaught exceptions
      process.on('uncaughtException', (error) => {
        this.logger.error('Uncaught exception', {
          error: error.message,
          stack: error.stack
        });
        this.shutdown('UNCAUGHT_EXCEPTION');
      });

      // Handle unhandled promise rejections
      process.on('unhandledRejection', (reason, promise) => {
        this.logger.error('Unhandled promise rejection', {
          reason: reason?.toString(),
          promise: promise?.toString()
        });
      });

    } catch (error) {
      this.logger.error('Failed to start Lightweight API Gateway', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    if (this.server) {
      // Stop accepting new connections
      this.server.close(() => {
        this.logger.info('Lightweight API Gateway stopped');
        process.exit(0);
      });

      // Force shutdown after 30 seconds
      setTimeout(() => {
        this.logger.error('Forced shutdown after timeout');
        process.exit(1);
      }, 30000);
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const gateway = new LightweightApiGateway();
  gateway.start().catch(error => {
    console.error('Failed to start Lightweight API Gateway:', error);
    process.exit(1);
  });
}

module.exports = LightweightApiGateway;