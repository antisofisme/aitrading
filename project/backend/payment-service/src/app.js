require('dotenv').config();

const express = require('express');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');

// Import configurations
const dbConnection = require('./config/database');
const redisConnection = require('./config/redis');
const logger = require('./config/logger');

// Import middleware
const security = require('./middleware/security');

// Import routes
const paymentRoutes = require('./routes/payments');
const subscriptionRoutes = require('./routes/subscriptions');

// Import controllers for health check
const PaymentController = require('./controllers/PaymentController');

class PaymentServiceApp {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3003;
    this.environment = process.env.NODE_ENV || 'development';

    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandlers();
  }

  /**
   * Setup application middleware
   */
  setupMiddleware() {
    // Trust proxy for rate limiting and IP detection
    this.app.set('trust proxy', 1);

    // Security headers (PCI DSS compliance)
    this.app.use(security.securityHeaders);

    // CORS configuration
    this.app.use(cors(security.corsOptions));

    // Request compression
    this.app.use(compression());

    // Request logging
    if (this.environment !== 'test') {
      this.app.use(morgan('combined', {
        stream: {
          write: (message) => logger.info(message.trim())
        }
      }));
    }

    // Audit logging (PCI DSS requirement)
    this.app.use(security.auditLogger);

    // Body parsing with size limits
    this.app.use(express.json({
      limit: '10mb',
      verify: (req, res, buf) => {
        req.rawBody = buf;
      }
    }));

    this.app.use(express.urlencoded({
      extended: true,
      limit: '10mb'
    }));

    // Request sanitization
    this.app.use(security.sanitizeRequest);

    // Rate limiting
    this.app.use('/api', security.apiRateLimit);
  }

  /**
   * Setup application routes
   */
  setupRoutes() {
    // Health check endpoint (no auth required)
    this.app.get('/health', PaymentController.healthCheck);
    this.app.get('/api/health', PaymentController.healthCheck);

    // API routes
    this.app.use('/api/payments', paymentRoutes);
    this.app.use('/api/subscriptions', subscriptionRoutes);

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        success: true,
        message: 'Neliti Payment Service API',
        version: '1.0.0',
        environment: this.environment,
        timestamp: new Date().toISOString(),
        endpoints: {
          health: '/health',
          payments: '/api/payments',
          subscriptions: '/api/subscriptions',
          webhook: '/api/payments/webhook'
        }
      });
    });

    // API documentation
    this.app.get('/api', (req, res) => {
      res.json({
        success: true,
        service: 'Payment Service',
        version: '1.0.0',
        description: 'Unified payment service with Midtrans integration for Indonesian market',
        features: [
          'Midtrans integration with all payment methods',
          'Indonesian payment methods (OVO, GoPay, DANA, LinkAja, ShopeePay)',
          'Subscription management with recurring billing',
          'Real-time webhook processing',
          'PCI DSS compliance',
          'Indonesian financial regulations compliance'
        ],
        endpoints: {
          'POST /api/payments': 'Create new payment',
          'GET /api/payments/:orderId': 'Get payment details',
          'GET /api/payments/user/history': 'Get user payment history',
          'PUT /api/payments/:orderId/cancel': 'Cancel payment',
          'GET /api/payments/:orderId/status': 'Check payment status',
          'POST /api/payments/webhook': 'Process Midtrans webhook',
          'GET /api/payments/methods/available': 'Get available payment methods',
          'GET /api/subscriptions/plans': 'Get subscription plans',
          'POST /api/subscriptions/create': 'Create subscription',
          'GET /api/subscriptions/user/active': 'Get user subscriptions',
          'PUT /api/subscriptions/:id/cancel': 'Cancel subscription'
        },
        authentication: 'Bearer token or X-Service-Token header',
        documentation: 'https://docs.neliti.com/payment-service'
      });
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        success: false,
        message: 'Endpoint not found',
        requestedPath: req.originalUrl,
        method: req.method,
        availableEndpoints: [
          'GET /health',
          'GET /api',
          'POST /api/payments',
          'GET /api/payments/:orderId',
          'POST /api/payments/webhook',
          'GET /api/subscriptions/plans'
        ]
      });
    });
  }

  /**
   * Setup error handlers
   */
  setupErrorHandlers() {
    // CORS error handler
    this.app.use((err, req, res, next) => {
      if (err.message && err.message.includes('CORS')) {
        logger.warn('🚫 CORS error', {
          origin: req.get('Origin'),
          method: req.method,
          path: req.path
        });

        return res.status(403).json({
          success: false,
          message: 'CORS policy violation',
          error: 'Origin not allowed'
        });
      }
      next(err);
    });

    // Validation error handler
    this.app.use((err, req, res, next) => {
      if (err.type === 'entity.parse.failed') {
        logger.warn('🚫 JSON parse error', {
          error: err.message,
          body: req.body
        });

        return res.status(400).json({
          success: false,
          message: 'Invalid JSON format',
          error: 'Request body must be valid JSON'
        });
      }
      next(err);
    });

    // Request size error handler
    this.app.use((err, req, res, next) => {
      if (err.type === 'entity.too.large') {
        logger.warn('🚫 Request too large', {
          size: err.length,
          limit: err.limit
        });

        return res.status(413).json({
          success: false,
          message: 'Request entity too large',
          error: 'Request body exceeds size limit'
        });
      }
      next(err);
    });

    // MongoDB/Mongoose error handler
    this.app.use((err, req, res, next) => {
      if (err.name === 'MongoError' || err.name === 'MongoServerError') {
        logger.error('❌ Database error', {
          error: err.message,
          code: err.code
        });

        return res.status(500).json({
          success: false,
          message: 'Database operation failed',
          error: this.environment === 'development' ? err.message : 'Internal server error'
        });
      }
      next(err);
    });

    // JWT error handler
    this.app.use((err, req, res, next) => {
      if (err.name === 'JsonWebTokenError') {
        logger.warn('🚫 JWT error', {
          error: err.message,
          token: req.headers.authorization?.substring(0, 20) + '...'
        });

        return res.status(401).json({
          success: false,
          message: 'Invalid authentication token',
          error: 'Token verification failed'
        });
      }
      next(err);
    });

    // Generic error handler
    this.app.use((err, req, res, next) => {
      logger.error('❌ Unhandled error', {
        error: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method,
        ip: req.ip
      });

      const statusCode = err.statusCode || err.status || 500;
      const message = err.message || 'Internal server error';

      res.status(statusCode).json({
        success: false,
        message: this.environment === 'development' ? message : 'Internal server error',
        error: this.environment === 'development' ? {
          name: err.name,
          message: err.message,
          stack: err.stack
        } : undefined,
        timestamp: new Date().toISOString()
      });
    });
  }

  /**
   * Initialize database connections
   */
  async initializeConnections() {
    try {
      // Connect to MongoDB
      await dbConnection.connect();
      logger.info('✅ MongoDB connection established');

      // Connect to Redis
      await redisConnection.connect();
      logger.info('✅ Redis connection established');

      // Verify Midtrans configuration
      const midtransConfig = require('./config/midtrans');
      logger.info('✅ Midtrans configuration verified', {
        environment: midtransConfig.getEnvironment()
      });

    } catch (error) {
      logger.error('❌ Failed to initialize connections', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Start the server
   */
  async start() {
    try {
      // Initialize connections
      await this.initializeConnections();

      // Start server
      const server = this.app.listen(this.port, () => {
        logger.info('🚀 Payment Service started successfully', {
          port: this.port,
          environment: this.environment,
          nodeVersion: process.version,
          timestamp: new Date().toISOString()
        });

        logger.info('📋 Service endpoints available:', {
          health: `http://localhost:${this.port}/health`,
          api: `http://localhost:${this.port}/api`,
          payments: `http://localhost:${this.port}/api/payments`,
          subscriptions: `http://localhost:${this.port}/api/subscriptions`,
          webhook: `http://localhost:${this.port}/api/payments/webhook`
        });
      });

      // Graceful shutdown
      this.setupGracefulShutdown(server);

      return server;

    } catch (error) {
      logger.error('❌ Failed to start Payment Service', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  /**
   * Setup graceful shutdown
   */
  setupGracefulShutdown(server) {
    const gracefulShutdown = async (signal) => {
      logger.info(`📤 Received ${signal}. Starting graceful shutdown...`);

      server.close(async () => {
        logger.info('🔒 HTTP server closed');

        try {
          // Close database connections
          await dbConnection.disconnect();
          logger.info('📤 MongoDB disconnected');

          await redisConnection.disconnect();
          logger.info('📤 Redis disconnected');

          logger.info('✅ Graceful shutdown completed');
          process.exit(0);

        } catch (error) {
          logger.error('❌ Error during shutdown', {
            error: error.message
          });
          process.exit(1);
        }
      });

      // Force shutdown after 30 seconds
      setTimeout(() => {
        logger.error('⚠️ Forced shutdown after timeout');
        process.exit(1);
      }, 30000);
    };

    // Handle shutdown signals
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('❌ Uncaught Exception', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('❌ Unhandled Rejection', {
        reason: reason,
        promise: promise
      });
      process.exit(1);
    });
  }

  /**
   * Get Express app instance
   */
  getApp() {
    return this.app;
  }
}

// Create and export app instance
const paymentService = new PaymentServiceApp();

// Start server if not in test environment
if (process.env.NODE_ENV !== 'test') {
  paymentService.start().catch((error) => {
    logger.error('❌ Failed to start application', {
      error: error.message,
      stack: error.stack
    });
    process.exit(1);
  });
}

module.exports = paymentService;